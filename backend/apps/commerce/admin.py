from django.contrib import admin
from .models import Plan, Subscription, Payment, Coupon


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "billing_cycle", "is_active", "is_featured", "sort_order"]
    list_editable = ["is_active", "is_featured", "sort_order"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "status", "started_at", "expires_at"]
    list_filter = ["status", "plan"]
    search_fields = ["user__email"]
    raw_id_fields = ["user", "plan"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["user", "amount", "currency", "gateway", "status", "reference", "paid_at", "created_at"]
    list_filter = ["status", "gateway", "currency"]
    search_fields = ["user__email", "reference", "transaction_id", "phone_number"]
    raw_id_fields = ["user", "subscription"]
    readonly_fields = ["raw_response", "created_at", "updated_at"]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ["code", "discount_type", "discount_value", "used_count", "max_uses", "is_active", "valid_from", "valid_until"]
    list_filter = ["discount_type", "is_active"]
    search_fields = ["code"]
