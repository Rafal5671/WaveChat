import json
import logging
import os

import redis
from dotenv import load_dotenv
from tasks import process_message_event

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/4")
CHANNEL = "chat:message_events"


def start():
    """
    Subscribe to Redis Pub/Sub channel and dispatch message events to Celery.

    Runs indefinitely — designed to be started as a separate process.
    Reconnects automatically on connection loss.
    """
    client = redis.from_url(REDIS_URL)
    pubsub = client.pubsub()
    pubsub.subscribe(CHANNEL)

    logger.info(f"Listening on Redis channel: {CHANNEL}")

    for raw_message in pubsub.listen():
        if raw_message["type"] != "message":
            continue

        try:
            event_data = json.loads(raw_message["data"])
            logger.info(f"Received message event: {event_data.get('message_id')}")
            process_message_event.delay(event_data)
        except json.JSONDecodeError:
            logger.error("Failed to decode message event — invalid JSON.")
        except Exception as e:
            logger.error(f"Failed to dispatch event to Celery: {e}")


if __name__ == "__main__":
    start()
