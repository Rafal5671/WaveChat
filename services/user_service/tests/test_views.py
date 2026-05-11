import uuid

import pytest
from faker import Faker

fake = Faker()


@pytest.mark.django_db
class TestCreateProfileView:
    """Tests for the CreateProfileView endpoint."""

    def test_create_profile_success(self, auth_client, user_id):
        """Profile is created with valid data."""
        response = auth_client.post(
            "/api/users/profile/create/",
            {
                "username": "newuser",
                "display_name": "New User",
            },
        )
        assert response.status_code == 201
        assert response.data["username"] == "newuser"

    def test_create_profile_duplicate(self, auth_client, own_profile):
        """Creating profile twice returns 409."""
        response = auth_client.post(
            "/api/users/profile/create/",
            {
                "username": "anotheruser",
                "display_name": "Another User",
            },
        )
        assert response.status_code == 409

    def test_create_profile_invalid_username(self, auth_client, user_id):
        """Username with invalid characters returns 400."""
        response = auth_client.post(
            "/api/users/profile/create/",
            {
                "username": "user name!",
                "display_name": "User",
            },
        )
        assert response.status_code == 400

    def test_create_profile_unauthenticated(self, api_client):
        """Unauthenticated request returns 401 or 403."""
        response = api_client.post(
            "/api/users/profile/create/",
            {
                "username": "user",
                "display_name": "User",
            },
        )
        assert response.status_code in [401, 403]


@pytest.mark.django_db
class TestOwnProfileView:
    """Tests for the OwnProfileView endpoint."""

    def test_get_own_profile(self, auth_client, own_profile):
        """Returns own profile data."""
        response = auth_client.get("/api/users/profile/")
        assert response.status_code == 200
        assert response.data["username"] == own_profile.username

    def test_get_own_profile_not_found(self, auth_client):
        """Returns 404 when profile doesn't exist."""
        response = auth_client.get("/api/users/profile/")
        assert response.status_code == 404

    def test_update_own_profile(self, auth_client, own_profile):
        """Profile is updated with valid data."""
        response = auth_client.patch(
            "/api/users/profile/",
            {
                "display_name": "Updated Name",
                "bio": "Updated bio",
            },
        )
        assert response.status_code == 200
        assert response.data["display_name"] == "Updated Name"
        assert response.data["bio"] == "Updated bio"


@pytest.mark.django_db
class TestPublicProfileView:
    """Tests for the PublicProfileView endpoint."""

    def test_get_public_profile(self, auth_client, other_profile):
        """Returns public profile for valid user ID."""
        response = auth_client.get(f"/api/users/profile/{other_profile.id}/")
        assert response.status_code == 200
        assert response.data["username"] == other_profile.username

    def test_get_nonexistent_profile(self, auth_client):
        """Returns 404 for nonexistent user ID."""
        response = auth_client.get(f"/api/users/profile/{uuid.uuid4()}/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestSearchProfilesView:
    """Tests for the SearchProfilesView endpoint."""

    def test_search_returns_results(self, auth_client, own_profile, other_profile):
        """Search returns matching profiles."""
        response = auth_client.get(
            f"/api/users/profile/search/?q={other_profile.username[:3]}"
        )
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_search_excludes_own_profile(self, auth_client, own_profile):
        """Search does not return own profile."""
        response = auth_client.get(
            f"/api/users/profile/search/?q={own_profile.username[:3]}"
        )
        assert response.status_code == 200
        ids = [p["id"] for p in response.data]
        assert str(own_profile.id) not in ids

    def test_search_too_short_query(self, auth_client):
        """Query shorter than 2 characters returns 400."""
        response = auth_client.get("/api/users/profile/search/?q=a")
        assert response.status_code == 400


@pytest.mark.django_db
class TestContactListView:
    """Tests for the ContactListView endpoint."""

    def test_add_contact(self, auth_client, own_profile, other_profile):
        """Contact is added successfully."""
        response = auth_client.post(
            "/api/users/contacts/",
            {
                "user_id": str(other_profile.id),
            },
        )
        assert response.status_code == 201

    def test_add_self_as_contact(self, auth_client, own_profile):
        """Cannot add self as contact."""
        response = auth_client.post(
            "/api/users/contacts/",
            {
                "user_id": str(own_profile.id),
            },
        )
        assert response.status_code == 400

    def test_get_contacts(self, auth_client, own_profile, other_profile):
        """Returns list of contacts."""
        from profiles.models import Contact

        Contact.objects.create(owner=own_profile, contact=other_profile)
        response = auth_client.get("/api/users/contacts/")
        assert response.status_code == 200
        assert len(response.data) == 1
