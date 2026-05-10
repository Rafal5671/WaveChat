from django.urls import path

from .views import (
    BlockUserView,
    ContactDetailView,
    ContactListView,
    CreateProfileView,
    OwnProfileView,
    PublicProfileView,
    SearchProfilesView,
    UpdateOnlineStatusView,
)

urlpatterns = [
    path("profile/", OwnProfileView.as_view(), name="own-profile"),
    path("profile/create/", CreateProfileView.as_view(), name="create-profile"),
    path("profile/search/", SearchProfilesView.as_view(), name="search-profiles"),
    path("profile/<uuid:user_id>/", PublicProfileView.as_view(), name="public-profile"),
    path("contacts/", ContactListView.as_view(), name="contacts"),
    path(
        "contacts/<uuid:contact_id>/",
        ContactDetailView.as_view(),
        name="contact-detail",
    ),
    path("contacts/block/<uuid:user_id>/", BlockUserView.as_view(), name="block-user"),
    path("status/", UpdateOnlineStatusView.as_view(), name="update-status"),
]
