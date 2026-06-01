"""Commerce app models: Plan, Subscription, Payment."""
import uuid
from django.db import models
from django.utils import timezone

from core.models import BaseModel, TimeStampedModel


class Plan(BaseModel):
    """Subscription tier (Free, Monthly, Annual)."""

    class BillingCycle(models.TextChoices):
        MONTHLY = "monthly", "Monthly"
        ANNUAL = "annual", "Annual"
        LIFETIME = "lifetime", "Lifetime"

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    billing_cycle = models.CharField(max_length=20, choices=BillingCycle.choices, default=BillingCycle.MONTHLY)
    features = models.JSONField(default=list, help_text='["Unlimited downloads", "All subjects"]')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "commerce_plans"
        ordering = ["sort_order", "price"]

    def __str__(self):
        return f"{self.name} ({self.get_billing_cycle_display()})"


class Subscription(TimeStampedModel):
    """User subscription to a plan."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"
        PENDING = "pending", "Pending Payment"

    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    auto_renew = models.BooleanField(default=True)

    class Meta:
        db_table = "commerce_subscriptions"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status", "expires_at"])]

    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"

    @property
    def is_active(self):
        return (
            self.status == self.Status.ACTIVE
            and (self.expires_at is None or self.expires_at > timezone.now())
        )


class Payment(BaseModel):
    """Payment record for subscription purchases."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"
        CANCELLED = "cancelled", "Cancelled"

    class Gateway(models.TextChoices):
        MPESA = "mpesa", "M-Pesa"
        CARD = "card", "Card"
        BANK = "bank", "Bank Transfer"
        FREE = "free", "Free"

    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="payments"
    )
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    )
    plan = models.ForeignKey(
        Plan, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments",
        help_text="Plan being purchased (denormalized for callback lookup).",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="KES")
    gateway = models.CharField(max_length=20, choices=Gateway.choices, default=Gateway.MPESA)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    reference = models.CharField(max_length=100, unique=True, blank=True)
    merchant_request_id = models.CharField(max_length=200, blank=True, db_index=True)
    transaction_id = models.CharField(max_length=200, blank=True, null=True, unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = "commerce_payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.amount} {self.currency} ({self.status})"


class Coupon(BaseModel):
    """Discount coupon."""

    class DiscountType(models.TextChoices):
        PERCENT = "percent", "Percentage"
        FIXED = "fixed", "Fixed Amount"

    code = models.CharField(max_length=50, unique=True, db_index=True)
    discount_type = models.CharField(max_length=10, choices=DiscountType.choices)
    discount_value = models.DecimalField(max_digits=8, decimal_places=2)
    max_uses = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)
    applicable_plans = models.ManyToManyField(Plan, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "commerce_coupons"

    def __str__(self):
        return f"{self.code} ({self.discount_value}{'' if self.discount_type == 'fixed' else '%'} off)"

    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_from > now:
            return False
        if self.valid_until and self.valid_until < now:
            return False
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        return True
