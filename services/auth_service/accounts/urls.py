from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    ValidateTokenView,
    VerifyPhoneView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-phone/", VerifyPhoneView.as_view(), name="verify-phone"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("validate/", ValidateTokenView.as_view(), name="validate-token"),
]
