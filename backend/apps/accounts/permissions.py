"""Accounts app — role and owner-level permissions."""
from rest_framework.permissions import BasePermission, SAFE_METHODS

from core.permissions import IsOwnerOrAdmin


class CanManageOwnAccount(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return IsOwnerOrAdmin().has_object_permission(request, view, obj)


class CanViewOwnProfile(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class CanManageUsers(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


class CanAccessPremium(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == "admin":
            return True
        return request.user.subscriptions.filter(status="active").exists()


class ReadOnlyUnlessAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")
