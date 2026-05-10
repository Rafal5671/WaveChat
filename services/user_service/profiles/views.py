from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Contact, Profile
from .serializers import (
    ContactSerializer,
    CreateProfileSerializer,
    ProfileSerializer,
    PublicProfileSerializer,
)


class CreateProfileView(APIView):
    """
    Create a profile after successful registration in auth_service.

    Called automatically by the frontend after receiving JWT tokens.
    The profile id must match the user UUID from auth_service.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create a new profile for the authenticated user."""
        if Profile.objects.filter(id=request.user.id).exists():
            return Response(
                {"error": "Profile already exists."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = CreateProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save(
            id=request.user.id,
        )

        return Response(
            ProfileSerializer(profile).data,
            status=status.HTTP_201_CREATED,
        )


class OwnProfileView(APIView):
    """Retrieve or update the currently authenticated user's profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return own profile data."""
        profile = get_object_or_404(Profile, id=request.user.id)
        return Response(ProfileSerializer(profile).data)

    def patch(self, request):
        """Partially update own profile."""
        profile = get_object_or_404(Profile, id=request.user.id)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Invalidate cache
        cache.delete(f"profile:{request.user.id}")

        return Response(serializer.data)


class PublicProfileView(APIView):
    """Retrieve a public profile by user ID."""

    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        """Return public profile data for the given user ID."""
        cache_key = f"profile:{user_id}"
        cached = cache.get(cache_key)

        if cached:
            return Response(cached)

        profile = get_object_or_404(Profile, id=user_id)
        data = PublicProfileSerializer(profile).data

        cache.set(cache_key, data, timeout=300)
        return Response(data)


class SearchProfilesView(APIView):
    """Search users by username or phone number."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return profiles matching the search query."""
        query = request.query_params.get("q", "").strip()

        if len(query) < 2:
            return Response(
                {"error": "Query must be at least 2 characters."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profiles = Profile.objects.filter(username__icontains=query).exclude(
            id=request.user.id
        )[:20]

        return Response(PublicProfileSerializer(profiles, many=True).data)


class ContactListView(APIView):
    """List all contacts or add a new contact."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return all contacts for the authenticated user."""
        contacts = Contact.objects.filter(
            owner__id=request.user.id,
            is_blocked=False,
        ).select_related("contact")

        return Response(ContactSerializer(contacts, many=True).data)

    def post(self, request):
        """Add a new contact by user ID."""
        contact_id = request.data.get("user_id")

        if not contact_id:
            return Response(
                {"error": "user_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if str(contact_id) == str(request.user.id):
            return Response(
                {"error": "You cannot add yourself as a contact."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        owner = get_object_or_404(Profile, id=request.user.id)
        contact_profile = get_object_or_404(Profile, id=contact_id)

        if Contact.objects.filter(owner=owner, contact=contact_profile).exists():
            return Response(
                {"error": "Contact already exists."},
                status=status.HTTP_409_CONFLICT,
            )

        contact = Contact.objects.create(owner=owner, contact=contact_profile)
        return Response(
            ContactSerializer(contact).data,
            status=status.HTTP_201_CREATED,
        )


class ContactDetailView(APIView):
    """Update or delete a specific contact."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, contact_id):
        """Update contact nickname or blocked status."""
        contact = get_object_or_404(
            Contact,
            id=contact_id,
            owner__id=request.user.id,
        )
        serializer = ContactSerializer(contact, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, contact_id):
        """Remove a contact."""
        contact = get_object_or_404(
            Contact,
            id=contact_id,
            owner__id=request.user.id,
        )
        contact.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BlockUserView(APIView):
    """Block or unblock a contact."""

    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        """Block the specified user."""
        owner = get_object_or_404(Profile, id=request.user.id)
        contact_profile = get_object_or_404(Profile, id=user_id)

        contact, created = Contact.objects.get_or_create(
            owner=owner,
            contact=contact_profile,
        )
        contact.is_blocked = True
        contact.save()

        return Response({"message": "User blocked successfully."})

    def delete(self, request, user_id):
        """Unblock the specified user."""
        contact = get_object_or_404(
            Contact,
            owner__id=request.user.id,
            contact__id=user_id,
        )
        contact.is_blocked = False
        contact.save()

        return Response({"message": "User unblocked successfully."})
