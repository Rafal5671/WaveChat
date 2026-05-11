import json
from unittest.mock import MagicMock, patch

import pytest


class TestSendPushNotification:
    """Tests for the send_push_notification task."""

    def test_send_returns_sent_count(self, mock_redis):
        """Returns sent count equal to number of users."""
        from tasks import send_push_notification

        result = send_push_notification(
            user_ids=["user-1", "user-2"],
            title="Test",
            body="Hello",
        )
        assert result == {"sent": 2}

    def test_send_empty_users_returns_zero(self, mock_redis):
        """Returns sent=0 when no users provided."""
        from tasks import send_push_notification

        result = send_push_notification(
            user_ids=[],
            title="Test",
            body="Hello",
        )
        assert result == {"sent": 0}

    def test_publishes_to_redis(self, mock_redis, user_id):
        """Publishes notification to Redis channel."""
        from tasks import deliver_browser_notification

        deliver_browser_notification(
            user_ids=[user_id],
            title="New message",
            body="Hello!",
            data={"type": "new_message"},
        )

        mock_redis.publish.assert_called_once_with(
            f"notifications:{user_id}",
            json.dumps(
                {
                    "type": "notification",
                    "title": "New message",
                    "body": "Hello!",
                    "data": {"type": "new_message"},
                }
            ),
        )

    def test_publishes_to_multiple_users(self, mock_redis):
        """Publishes notification to each user's channel."""
        from tasks import deliver_browser_notification

        user_ids = ["user-1", "user-2", "user-3"]

        deliver_browser_notification(
            user_ids=user_ids,
            title="Test",
            body="Hello",
            data={},
        )

        assert mock_redis.publish.call_count == 3


class TestProcessMessageEvent:
    """Tests for the process_message_event task."""

    def test_skips_when_no_participants_cache(self, mock_redis):
        """Does nothing when participants cache is missing."""
        mock_redis.get.return_value = None

        from tasks import process_message_event

        process_message_event(
            {
                "conversation_id": "conv-1",
                "sender_id": "user-1",
                "content": "Hello",
                "message_id": "msg-1",
            }
        )

        mock_redis.publish.assert_not_called()

    def test_skips_online_participants(self, mock_redis):
        """Does not notify participants who are online."""
        mock_redis.smembers.return_value = {b"user-2"}
        mock_redis.get.return_value = json.dumps(
            [
                {"user_id": "user-1"},
                {"user_id": "user-2"},
            ]
        ).encode()

        from tasks import process_message_event

        process_message_event(
            {
                "conversation_id": "conv-1",
                "sender_id": "user-1",
                "content": "Hello",
                "message_id": "msg-1",
            }
        )

        mock_redis.publish.assert_not_called()

    def test_notifies_offline_participants(self, mock_redis):
        """Notifies participants who are offline."""
        mock_redis.smembers.return_value = set()
        mock_redis.get.return_value = json.dumps(
            [
                {"user_id": "user-1"},
                {"user_id": "user-2"},
            ]
        ).encode()

        with patch("tasks.send_push_notification") as mock_task:
            mock_task.delay = MagicMock()

            from tasks import process_message_event

            process_message_event(
                {
                    "conversation_id": "conv-1",
                    "sender_id": "user-1",
                    "content": "Hello",
                    "message_id": "msg-1",
                }
            )

            mock_task.delay.assert_called_once()
            call_kwargs = mock_task.delay.call_args
            assert "user-2" in call_kwargs.kwargs["user_ids"]

    def test_truncates_long_content(self, mock_redis):
        """Long message content is truncated in notification body."""
        mock_redis.smembers.return_value = set()
        mock_redis.get.return_value = json.dumps(
            [
                {"user_id": "user-1"},
                {"user_id": "user-2"},
            ]
        ).encode()

        long_content = "x" * 200

        with patch("tasks.send_push_notification") as mock_task:
            mock_task.delay = MagicMock()

            from tasks import process_message_event

            process_message_event(
                {
                    "conversation_id": "conv-1",
                    "sender_id": "user-1",
                    "content": long_content,
                    "message_id": "msg-1",
                }
            )

            call_kwargs = mock_task.delay.call_args
            assert len(call_kwargs.kwargs["body"]) <= 103
