"""Notifications views."""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from django.utils import timezone

from core.pagination import StandardResultsPagination
from core.responses import success_response, error_response
from . import services
from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(ReadOnlyModelViewSet):
    """
    GET    /notifications/                  List notifications (?unread=true)
    GET    /notifications/{id}/             Detail
    POST   /notifications/mark-all-read/    Mark all as read
    POST   /notifications/{id}/read/        Mark one as read
    GET    /notifications/unread-count/     Unread count
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        if self.request.query_params.get("unread") == "true":
            qs = qs.filter(is_read=False)
        return qs.order_by("-created_at")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(data=self.get_serializer(queryset, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(data=self.get_serializer(self.get_object()).data)

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        """GET /notifications/unread-count/"""
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return success_response(data={"unread_count": count})

    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        """POST /notifications/{id}/read/"""
        notif = self.get_object()
        notif.is_read = True
        notif.read_at = timezone.now()
        notif.save(update_fields=["is_read", "read_at"])
        return success_response(message="Marked as read.")

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        """POST /notifications/mark-all-read/"""
        count = services.mark_all_read(request.user)
        return success_response(
            data={"marked_read": count},
            message=f"{count} notification(s) marked as read.",
        )
