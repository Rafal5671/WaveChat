import requests
from django.conf import settings


class SimpleUser:
    """
    Lightweight user object for WebSocket scope.

    Injected into scope['user'] by JWTAuthMiddleware.
    The pk attribute is required by DRF throttling.
    """

    def __init__(self, user_id: str, email: str, is_verified: bool):
        """Initialize user with claims from auth_service."""
        self.id = user_id
        self.pk = user_id
        self.email = email
        self.is_verified = is_verified
        self.is_authenticated = True

    def __str__(self):
        return self.email


class JWTAuthMiddleware:
    """
    ASGI middleware that validates JWT tokens for WebSocket connections.

    Extracts token from query string (?token=<jwt>) and validates it
    against auth_service. Injects SimpleUser into scope['user'].
    If token is missing or invalid, scope['user'] is set to None.
    """

    def __init__(self, inner):
        """Store the inner ASGI application."""
        self.inner = inner

    async def __call__(self, scope, receive, send):
        """Validate token and inject user into scope before passing on."""
        if scope["type"] == "websocket":
            token = self._extract_token(scope)
            scope["user"] = None

            if token:
                user = await self._validate_token(token)
                scope["user"] = user

        return await self.inner(scope, receive, send)

    def _extract_token(self, scope):
        """Extract JWT from WebSocket query string."""
        query_string = scope.get("query_string", b"").decode()
        for param in query_string.split("&"):
            if param.startswith("token="):
                return param.split("=", 1)[1]
        return None

    async def _validate_token(self, token):
        """Call auth_service to validate token and return SimpleUser or None."""
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(
                    f"{settings.AUTH_SERVICE_URL}/api/auth/validate/",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=3,
                ),
            )
            if response.status_code == 200:
                data = response.json()
                return SimpleUser(
                    user_id=data["user_id"],
                    email=data["email"],
                    is_verified=data["is_verified"],
                )
        except Exception:
            return None
        return None
