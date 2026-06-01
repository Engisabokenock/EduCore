"""Notifications app models."""
from django.db import models

from core.models import BaseModel


class Notification(BaseModel):
    """In-app notification for a user."""

    class Channel(models.TextChoices):
        IN_APP = "in_app", "In-App"
        EMAIL = "email", "Email"
        WHATSAPP = "whatsapp", "WhatsApp"
        PUSH = "push", "Push"

    class NotificationType(models.TextChoices):
        SYSTEM = "system", "System"
        PAYMENT = "payment", "Payment"
        SUBSCRIPTION = "subscription", "Subscription"
        CONTENT = "content", "Content"
        REVIEW = "review", "Review"

    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices, db_index=True)
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.IN_APP)
    title = models.CharField(max_length=200)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read"])]

    def __str__(self):
        return f"{self.user.email}: {self.title}"
