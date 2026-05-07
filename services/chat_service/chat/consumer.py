import json
import uuid

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from .models import Conversation, ConversationParticipant, Message
from .serializers import MessageSerializer


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer handling real-time messaging for a single conversation.

    Connection URL: ws://host/ws/chat/<conversation_id>/?token=<jwt>

    Supported incoming message types:
        - message: send a new text or media message
        - typing: broadcast typing indicator to other participants
        - read: mark a message as read and notify sender

    Supported outgoing message types:
        - history: recent messages sent on connect
        - message: new message broadcast to all participants
        - typing: typing indicator from another participant
        - read_receipt: read confirmation for a message
        - error: error details when an action fails
    """

    async def connect(self):
        """Authenticate user, verify participation and join channel group."""
        user = self.scope.get("user")

        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.user_id = str(user.id)
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group = f"chat_{self.conversation_id}"

        is_participant = await self._check_participant()
        if not is_participant:
            await self.close(code=4004)
            return

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

        messages = await self._get_recent_messages()
        await self.send(
            text_data=json.dumps(
                {
                    "type": "history",
                    "messages": messages,
                }
            )
        )

    async def disconnect(self, close_code):
        """Leave channel group and update last seen timestamp."""
        if hasattr(self, "room_group"):
            await self.channel_layer.group_discard(self.room_group, self.channel_name)

        if hasattr(self, "conversation_id") and hasattr(self, "user_id"):
            await self._update_last_seen()

    async def receive(self, text_data):
        """Route incoming WebSocket messages to appropriate handlers."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self._send_error("Invalid JSON format.")
            return

        msg_type = data.get("type")

        if msg_type == "message":
            await self._handle_message(data)
        elif msg_type == "typing":
            await self._handle_typing(data)
        elif msg_type == "read":
            await self._handle_read(data)
        else:
            await self._send_error(f"Unknown message type: {msg_type}")

    # ── Incoming message handlers ─────────────────────────────

    async def _handle_message(self, data):
        """Validate, save and broadcast a new message."""
        content = data.get("content", "").strip()
        message_type = data.get("message_type", "text")
        reply_to_id = data.get("reply_to")

        if not content and message_type == "text":
            await self._send_error("Message content cannot be empty.")
            return

        message = await self._save_message(content, message_type, reply_to_id)

        await self.channel_layer.group_send(
            self.room_group,
            {
                "type": "chat.message",
                "message": {
                    "id": str(message.id),
                    "conversation_id": self.conversation_id,
                    "sender_id": self.user_id,
                    "content": message.content,
                    "message_type": message.message_type,
                    "reply_to": reply_to_id,
                    "created_at": message.created_at.isoformat(),
                    "status": "sent",
                },
            },
        )

    async def _handle_typing(self, data):
        """Broadcast typing indicator to other participants."""
        await self.channel_layer.group_send(
            self.room_group,
            {
                "type": "chat.typing",
                "user_id": self.user_id,
                "is_typing": data.get("is_typing", False),
            },
        )

    async def _handle_read(self, data):
        """Mark a message as read and notify all participants."""
        message_id = data.get("message_id")

        if not message_id:
            await self._send_error("message_id is required.")
            return

        await self._mark_message_read(message_id)

        await self.channel_layer.group_send(
            self.room_group,
            {
                "type": "chat.read",
                "message_id": message_id,
                "reader_id": self.user_id,
                "read_at": timezone.now().isoformat(),
            },
        )

    # ── Channel layer event handlers ──────────────────────────

    async def chat_message(self, event):
        """Forward broadcast message to WebSocket client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "message",
                    **event["message"],
                }
            )
        )

    async def chat_typing(self, event):
        """Forward typing indicator — skip if sent by current user."""
        if event["user_id"] == self.user_id:
            return

        await self.send(
            text_data=json.dumps(
                {
                    "type": "typing",
                    "user_id": event["user_id"],
                    "is_typing": event["is_typing"],
                }
            )
        )

    async def chat_read(self, event):
        """Forward read receipt to WebSocket client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "read_receipt",
                    "message_id": event["message_id"],
                    "reader_id": event["reader_id"],
                    "read_at": event["read_at"],
                }
            )
        )

    # ── Helpers ───────────────────────────────────────────────

    async def _send_error(self, message):
        """Send an error message to the WebSocket client."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "message": message,
                }
            )
        )

    # ── Database helpers ──────────────────────────────────────

    @database_sync_to_async
    def _check_participant(self):
        """Check whether the current user is a participant in the conversation."""
        return ConversationParticipant.objects.filter(
            conversation_id=self.conversation_id,
            user_id=self.user_id,
        ).exists()

    @database_sync_to_async
    def _save_message(self, content, message_type, reply_to_id):
        """Persist a new message to the database."""
        return Message.objects.create(
            id=uuid.uuid4(),
            conversation_id=self.conversation_id,
            sender_id=self.user_id,
            content=content,
            message_type=message_type,
            reply_to_id=reply_to_id,
        )

    @database_sync_to_async
    def _get_recent_messages(self, limit=50):
        """Return the most recent messages for this conversation."""
        qs = Message.objects.filter(
            conversation_id=self.conversation_id,
            is_deleted=False,
        ).order_by("-created_at")[:limit]

        return MessageSerializer(reversed(list(qs)), many=True).data

    @database_sync_to_async
    def _mark_message_read(self, message_id):
        """Update message status to read."""
        Message.objects.filter(id=message_id).update(
            status="read",
            read_at=timezone.now(),
        )

    @database_sync_to_async
    def _update_last_seen(self):
        """Update the participant's last seen timestamp."""
        ConversationParticipant.objects.filter(
            conversation_id=self.conversation_id,
            user_id=self.user_id,
        ).update(last_seen=timezone.now())
