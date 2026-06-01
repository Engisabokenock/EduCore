from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="auth-register"),
    path("login/", views.login_view, name="auth-login"),
    path("logout/", views.logout_view, name="auth-logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("verify-email/", views.verify_email_view, name="auth-verify-email"),
    path("me/", views.MeView.as_view(), name="auth-me"),
    path("change-password/", views.change_password_view, name="auth-change-password"),
    path("forgot-password/", views.forgot_password_view, name="auth-forgot-password"),
    path("reset-password/", views.reset_password_view, name="auth-reset-password"),
]
