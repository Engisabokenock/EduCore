from rest_framework import serializers
from .models import Plan, Subscription, Payment, Coupon


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ["id", "name", "slug", "description", "price", "billing_cycle", "features", "is_featured", "sort_order"]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Subscription
        fields = ["id", "plan", "status", "started_at", "expires_at", "auto_renew", "is_active", "created_at"]


class InitiatePaymentSerializer(serializers.Serializer):
    plan_id = serializers.UUIDField()
    phone_number = serializers.CharField(max_length=20)
    coupon_code = serializers.CharField(required=False, allow_blank=True)

    def validate_phone_number(self, value):
        import re
        digits = re.sub(r"\D", "", value)
        if len(digits) < 9:
            raise serializers.ValidationError("Invalid phone number.")
        return digits


class PaymentSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "amount", "currency", "gateway", "status",
            "plan_name", "paid_at", "created_at",
        ]
        read_only_fields = fields


class PaymentAdminSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "amount", "currency", "gateway", "status",
            "reference", "transaction_id", "phone_number",
            "plan_name", "paid_at", "error_message", "created_at",
        ]
        read_only_fields = fields


class PaymentStatusSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "reference", "status", "gateway",
            "amount", "currency", "paid_at", "plan_name", "created_at",
        ]
        read_only_fields = fields
