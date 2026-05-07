from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation, ConversationParticipant, Message
from .serializers import (
    ConversationSerializer,
    CreateConversationSerializer,
    MessageSerializer,
)


class ConversationListView(APIView):
    """List all conversations for the current user or create a new one."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return all conversations the current user participates in."""
        conversation_ids = ConversationParticipant.objects.filter(
            user_id=request.user.id,
        ).values_list("conversation_id", flat=True)

        conversations = Conversation.objects.filter(
            id__in=conversation_ids,
        ).prefetch_related("participants")

        return Response(ConversationSerializer(conversations, many=True).data)

    def post(self, request):
        """Create a new direct or group conversation."""
        serializer = CreateConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        participant_ids = data["participant_ids"]

        # Prevent duplicate direct conversations
        if data["type"] == "direct":
            other_id = str(participant_ids[0])
            existing = ConversationParticipant.objects.filter(
                user_id=request.user.id,
            ).values_list("conversation_id", flat=True)

            duplicate = ConversationParticipant.objects.filter(
                conversation_id__in=existing,
                user_id=other_id,
                conversation__type="direct",
            ).first()

            if duplicate:
                conversation = duplicate.conversation
                return Response(
                    ConversationSerializer(conversation).data,
                    status=status.HTTP_200_OK,
                )

        conversation = Conversation.objects.create(
            type=data["type"],
            name=data.get("name", ""),
            created_by=request.user.id,
        )

        # Add creator as admin
        ConversationParticipant.objects.create(
            conversation=conversation,
            user_id=request.user.id,
            role="admin",
        )

        # Add other participants as members
        for pid in participant_ids:
            ConversationParticipant.objects.create(
                conversation=conversation,
                user_id=pid,
                role="member",
            )

        return Response(
            ConversationSerializer(conversation).data,
            status=status.HTTP_201_CREATED,
        )


class ConversationDetailView(APIView):
    """Retrieve or delete a specific conversation."""

    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        """Return conversation details if the user is a participant."""
        self._get_participant_or_403(conversation_id, request.user.id)
        conversation = get_object_or_404(
            Conversation.objects.prefetch_related("participants"),
            id=conversation_id,
        )
        return Response(ConversationSerializer(conversation).data)

    def delete(self, request, conversation_id):
        """Leave a conversation (or delete it if creator and group)."""
        participant = self._get_participant_or_403(conversation_id, request.user.id)
        participant.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _get_participant_or_403(self, conversation_id, user_id):
        """Return participant record or raise 403 if not a participant."""
        return get_object_or_404(
            ConversationParticipant,
            conversation_id=conversation_id,
            user_id=user_id,
        )


class MessageListView(APIView):
    """List messages in a conversation with cursor-based pagination."""

    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        """Return paginated messages for the conversation."""
        get_object_or_404(
            ConversationParticipant,
            conversation_id=conversation_id,
            user_id=request.user.id,
        )

        limit = min(int(request.query_params.get("limit", 50)), 100)
        before = request.query_params.get("before")

        messages = Message.objects.filter(
            conversation_id=conversation_id,
            is_deleted=False,
        )

        if before:
            messages = messages.filter(created_at__lt=before)

        messages = messages.order_by("-created_at")[:limit]

        return Response(MessageSerializer(reversed(list(messages)), many=True).data)


class MessageDetailView(APIView):
    """Edit or soft-delete a specific message."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, message_id):
        """Edit message content — only allowed for the sender."""
        message = get_object_or_404(Message, id=message_id)

        if str(message.sender_id) != str(request.user.id):
            return Response(
                {"error": "You can only edit your own messages."},
                status=status.HTTP_403_FORBIDDEN,
            )

        content = request.data.get("content", "").strip()
        if not content:
            return Response(
                {"error": "Content cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.utils import timezone

        message.content = content
        message.edited_at = timezone.now()
        message.save()

        return Response(MessageSerializer(message).data)

    def delete(self, request, message_id):
        """Soft-delete a message — only allowed for the sender."""
        message = get_object_or_404(Message, id=message_id)

        if str(message.sender_id) != str(request.user.id):
            return Response(
                {"error": "You can only delete your own messages."},
                status=status.HTTP_403_FORBIDDEN,
            )

        message.is_deleted = True
        message.content = ""
        message.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
