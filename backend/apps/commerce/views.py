"""Commerce views — Plans, Subscriptions, Payments."""
import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status, filters
from rest_framework.decorators import action, api_view, permission_classes as pc
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, GenericViewSet
from rest_framework.mixins import ListModelMixin

from core.pagination import StandardResultsPagination
from core.responses import success_response, created_response, error_response
from . import services
from .models import Plan, Subscription, Payment
from .serializers import (
    PlanSerializer,
    SubscriptionSerializer,
    InitiatePaymentSerializer,
    PaymentSerializer,
    PaymentStatusSerializer,
    CouponValidateSerializer,
)

logger = logging.getLogger("apps.commerce")


class PlanViewSet(ReadOnlyModelViewSet):
    """
    GET /commerce/plans/        List all active plans
    GET /commerce/plans/{slug}/ Plan detail
    """
    permission_classes = [AllowAny]
    serializer_class = PlanSerializer
    lookup_field = "slug"
    queryset = Plan.objects.filter(is_active=True).order_by("sort_order")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return success_response(data=self.get_serializer(queryset, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(data=self.get_serializer(self.get_object()).data)


class SubscriptionViewSet(ListModelMixin, GenericViewSet):
    """
    GET  /commerce/subscriptions/         My subscription history
    GET  /commerce/subscriptions/active/  Active subscription
    POST /commerce/subscriptions/pay/     Initiate payment (M-Pesa STK Push)
    POST /commerce/subscriptions/validate-coupon/ Validate coupon code
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionSerializer
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        return self.request.user.subscriptions.select_related("plan").order_by("-created_at")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(data=self.get_serializer(queryset, many=True).data)

    @action(detail=False, methods=["get"], url_path="active")
    def active(self, request):
        """GET /commerce/subscriptions/active/ — current active subscription."""
        sub = request.user.subscriptions.filter(status="active").order_by("-created_at").first()
        if not sub:
            return success_response(
                data=None,
                message="No active subscription. Visit /pricing to upgrade.",
            )
        return success_response(data=SubscriptionSerializer(sub).data)

    @action(detail=False, methods=["post"], url_path="pay")
    def pay(self, request):
        """
        POST /commerce/subscriptions/pay/
        Body: { plan_id, phone_number, coupon_code? }
        Initiates M-Pesa STK Push.
        """
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            plan = Plan.objects.get(id=data["plan_id"], is_active=True)
        except Plan.DoesNotExist:
            return error_response("Plan not found.", status_code=404)

        amount = services.calculate_discounted_price(plan, data.get("coupon_code", ""))
        payment = services.create_pending_payment(request.user, plan, data["phone_number"], amount)

        try:
            mpesa = services.initiate_mpesa_stk_push(
                phone=data["phone_number"],
                amount=amount,
                reference=payment.reference,
                description=f"EduCore {plan.name}",
            )
            # Store MerchantRequestID so the callback can look up this payment precisely
            merchant_request_id = mpesa.get("MerchantRequestID", "")
            payment.merchant_request_id = merchant_request_id
            payment.raw_response = mpesa
            payment.save(update_fields=["merchant_request_id", "raw_response"])
            return created_response(
                data={
                    "payment_reference": payment.reference,
                    "amount": str(amount),
                    "currency": "KES",
                    "phone_number": data["phone_number"],
                    "plan": PlanSerializer(plan).data,
                },
                message="STK Push sent. Complete the payment on your phone.",
            )
        except Exception as exc:
            logger.exception("STK push failed for payment %s", payment.reference)
            payment.status = Payment.Status.FAILED
            payment.error_message = str(exc)
            payment.save(update_fields=["status", "error_message"])
            return error_response(
                "Payment initiation failed. Please try again.",
                status_code=502,
            )

    @action(detail=False, methods=["post"], url_path="validate-coupon")
    def validate_coupon(self, request):
        """POST /commerce/subscriptions/validate-coupon/ — validate and preview coupon discount."""
        serializer = CouponValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            plan = Plan.objects.get(id=serializer.validated_data["plan_id"], is_active=True)
        except Plan.DoesNotExist:
            return error_response("Plan not found.", status_code=404)

        original = plan.price
        discounted = services.calculate_discounted_price(plan, serializer.validated_data["code"])
        saving = original - discounted

        if saving <= 0:
            return error_response("Coupon is invalid or not applicable to this plan.", status_code=400)

        return success_response(
            data={
                "code": serializer.validated_data["code"].upper(),
                "original_price": str(original),
                "discounted_price": str(discounted),
                "saving": str(saving),
            },
            message="Coupon applied successfully.",
        )


class PaymentViewSet(ListModelMixin, GenericViewSet):
    """
    GET /commerce/payments/         My payment history
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentSerializer
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        return self.request.user.payments.order_by("-created_at")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(data=self.get_serializer(queryset, many=True).data)


class PaymentStatusViewSet(ListModelMixin, GenericViewSet):
    """
    GET  /commerce/payments/status/              All statuses (admin) / own payments (user)
    GET  /commerce/payments/status/{reference}/  Single payment by reference
    POST /commerce/payments/status/check/        Poll status by reference (client)
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentStatusSerializer
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Payment.objects.select_related("user", "plan").order_by("-created_at")
        return Payment.objects.filter(user=user).select_related("plan").order_by("-created_at")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(data=self.get_serializer(queryset, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        # {pk} in the URL is used as the payment reference
        reference = kwargs.get("pk", "")
        payment = get_object_or_404(self.get_queryset(), reference=reference)
        return success_response(data=self.get_serializer(payment).data)

    @action(detail=False, methods=["post"], url_path="check")
    def check_status(self, request):
        """POST /commerce/payments/status/check/ — { reference } → current payment status."""

        class _Ref(serializers.Serializer):
            reference = serializers.CharField(max_length=100)

        s = _Ref(data=request.data)
        s.is_valid(raise_exception=True)
        payment = get_object_or_404(
            Payment.objects.select_related("plan"),
            reference=s.validated_data["reference"],
            user=request.user,
        )
        return success_response(data=self.get_serializer(payment).data)


def _get_client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


@api_view(["POST"])
@pc([AllowAny])
def mpesa_callback(request):
    """POST /commerce/callback/mpesa/ — M-Pesa async payment callback.

    Safaricom delivers this from a fixed IP range. Configure MPESA_ALLOWED_IPS
    in production to reject spoofed callbacks before they touch the database.
    """
    allowed_ips = [ip for ip in getattr(settings, "MPESA_ALLOWED_IPS", []) if ip]
    if allowed_ips:
        client_ip = _get_client_ip(request)
        if client_ip not in allowed_ips:
            logger.warning("M-Pesa callback rejected from unauthorized IP: %s", client_ip)
            # Return 200 so Safaricom stops retrying, but log the violation
            return Response({"ResultCode": 1, "ResultDesc": "Unauthorized"})

    services.handle_mpesa_callback(request.data)
    return Response({"ResultCode": 0, "ResultDesc": "Success"})
