from django.urls import path

from .views import (
    ConversationDetailView,
    ConversationListView,
    MessageDetailView,
    MessageListView,
)

urlpatterns = [
    path("conversations/", ConversationListView.as_view(), name="conversations"),
    path(
        "conversations/<uuid:conversation_id>/",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
    path(
        "conversations/<uuid:conversation_id>/messages/",
        MessageListView.as_view(),
        name="messages",
    ),
    path(
        "messages/<uuid:message_id>/",
        MessageDetailView.as_view(),
        name="message-detail",
    ),
]
