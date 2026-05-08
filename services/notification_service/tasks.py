import json
import logging
import os
from typing import Optional

import redis
from celery_app import app
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/4")


def _get_redis():
    """Return a Redis client instance."""
    return redis.from_url(REDIS_URL)


def deliver_browser_notification(
    user_ids: list[str], title: str, body: str, data: dict
):
    """
    Publish a browser notification event to Redis.

    The frontend subscribes to a per-user Redis channel via SSE or
    a dedicated WebSocket connection. When a message arrives on
    notifications:<user_id>, the browser displays a native
    Web Notification API popup.
    """
    r = _get_redis()

    payload = json.dumps(
        {
            "type": "notification",
            "title": title,
            "body": body,
            "data": data,
        }
    )

    for user_id in user_ids:
        channel = f"notifications:{user_id}"
        r.publish(channel, payload)
        logger.info(f"Published browser notification to {channel}")


@app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
    name="notifications.send_push",
)
def send_push_notification(
    self,
    user_ids: list[str],
    title: str,
    body: str,
    data: Optional[dict] = None,
):
    """
    Deliver a browser notification to a list of users via Redis Pub/Sub.

    The Vue.js frontend listens on a Server-Sent Events endpoint that
    subscribes to notifications:<user_id> Redis channel and forwards
    events to the browser Notification API.
    Retries up to 3 times with 10 second delay on failure.
    """
    try:
        deliver_browser_notification(
            user_ids=user_ids,
            title=title,
            body=body,
            data=data or {},
        )
        return {"sent": len(user_ids)}

    except Exception as exc:
        logger.error(f"Notification task failed: {exc}")
        raise self.retry(exc=exc)


@app.task(
    name="notifications.process_message_event",
    queue="notifications",
)
def process_message_event(event_data: dict):
    """
    Process a new message event and notify offline participants.

    Reads participant list and online users from Redis.
    Sends browser notification only to participants not currently
    connected via WebSocket to the chat room.
    """
    r = _get_redis()

    conversation_id = event_data.get("conversation_id")
    sender_id = event_data.get("sender_id")
    content = event_data.get("content", "")
    message_id = event_data.get("message_id")

    online_key = f"online:conv:{conversation_id}"
    online_users = {uid.decode() for uid in r.smembers(online_key)}

    participants_raw = r.get(f"participants:{conversation_id}")
    if not participants_raw:
        logger.warning(f"No participants cache for conversation {conversation_id}")
        return

    participants = json.loads(participants_raw)

    offline_user_ids = [
        p["user_id"]
        for p in participants
        if p["user_id"] != sender_id and p["user_id"] not in online_users
    ]

    if not offline_user_ids:
        logger.info("All participants online — skipping notification.")
        return

    body = content[:100] + "..." if len(content) > 100 else content

    send_push_notification.delay(
        user_ids=offline_user_ids,
        title="New message — WaveChat",
        body=body,
        data={
            "type": "new_message",
            "conversation_id": str(conversation_id),
            "message_id": str(message_id),
            "sender_id": str(sender_id),
        },
    )
