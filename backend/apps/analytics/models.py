"""Analytics app models: Event, ResourceView, LessonProgress."""
from django.db import models

from core.models import TimeStampedModel


class Event(models.Model):
    """Generic analytics event."""

    class EventType(models.TextChoices):
        PAGE_VIEW = "page_view", "Page View"
        RESOURCE_VIEW = "resource_view", "Resource View"
        RESOURCE_DOWNLOAD = "resource_download", "Resource Download"
        SEARCH = "search", "Search"
        REGISTER = "register", "Register"
        LOGIN = "login", "Login"
        SUBSCRIPTION = "subscription", "Subscription"
        PAYMENT = "payment", "Payment"

    user = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="events"
    )
    event_type = models.CharField(max_length=30, choices=EventType.choices, db_index=True)
    data = models.JSONField(default=dict, blank=True)
    session_id = models.CharField(max_length=64, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "analytics_events"
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["event_type", "timestamp"])]

    def __str__(self):
        return f"{self.event_type} at {self.timestamp}"


class DailyStats(models.Model):
    """Pre-aggregated daily statistics for dashboards."""
    date = models.DateField(unique=True, db_index=True)
    total_users = models.PositiveIntegerField(default=0)
    new_users = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    total_downloads = models.PositiveIntegerField(default=0)
    total_views = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    new_subscriptions = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "analytics_daily_stats"
        ordering = ["-date"]

    def __str__(self):
        return f"Stats for {self.date}"
