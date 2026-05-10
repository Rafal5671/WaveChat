import asyncio
import json
import os

import redis.asyncio as aioredis
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/4")
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")

app = FastAPI(
    title="WaveChat Notification SSE",
    description="Server-Sent Events endpoint for browser notifications.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


async def _validate_token(token: str) -> str | None:
    """
    Validate Bearer token against auth_service.

    Returns user_id string on success or None on failure.
    """
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/api/auth/validate/",
                headers={"Authorization": f"Bearer {token}"},
                timeout=3,
            )
            if response.status_code == 200:
                return response.json()["user_id"]
    except Exception:
        return None
    return None


async def _event_generator(user_id: str):
    """
    Subscribe to Redis Pub/Sub channel and yield SSE events.

    Yields a keepalive comment every 30 seconds to prevent
    the browser from closing the connection.
    """
    r = aioredis.from_url(REDIS_URL)
    pubsub = r.pubsub()
    channel = f"notifications:{user_id}"

    await pubsub.subscribe(channel)

    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=30,
            )

            if message and message["type"] == "message":
                data = message["data"]
                if isinstance(data, bytes):
                    data = data.decode()
                yield f"data: {data}\n\n"
            else:
                yield ": ping\n\n"

            await asyncio.sleep(0.1)

    finally:
        await pubsub.unsubscribe(channel)
        await r.aclose()


@app.get("/api/notifications/stream/")
async def notification_stream(
    authorization: str | None = Header(default=None),
    token: str | None = Query(default=None),
):
    """
    SSE endpoint for browser notifications.

    Accepts token via Authorization header or ?token= query parameter,
    since EventSource API does not support custom headers natively.
    Each event is a JSON object with type, title, body and data fields.
    """
    bearer_token = None

    if authorization and authorization.startswith("Bearer "):
        bearer_token = authorization[7:]
    elif token:
        bearer_token = token

    if not bearer_token:
        raise HTTPException(status_code=401, detail="Bearer token required.")

    user_id = await _validate_token(bearer_token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")

    return StreamingResponse(
        _event_generator(user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "notification_sse"}
