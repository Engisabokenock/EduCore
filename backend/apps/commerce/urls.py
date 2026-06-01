"""
Commerce URL routing.

    GET  /api/v1/commerce/plans/                          All subscription plans
    GET  /api/v1/commerce/plans/{slug}/                   Plan detail
    GET  /api/v1/commerce/subscriptions/                  My subscription history
    GET  /api/v1/commerce/subscriptions/active/           Active subscription
    POST /api/v1/commerce/subscriptions/pay/              Initiate M-Pesa payment
    POST /api/v1/commerce/subscriptions/validate-coupon/  Validate coupon
    GET  /api/v1/commerce/payments/                       My payment history
    POST /api/v1/commerce/callback/mpesa/                 M-Pesa async callback
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, SubscriptionViewSet, PaymentViewSet, PaymentStatusViewSet, mpesa_callback

router = DefaultRouter()
router.register(r"plans", PlanViewSet, basename="plan")
router.register(r"subscriptions", SubscriptionViewSet, basename="subscription")
router.register(r"payments", PaymentViewSet, basename="payment")
router.register(r"payments/status", PaymentStatusViewSet, basename="payment-status")

urlpatterns = [
    path("", include(router.urls)),
    path("callback/mpesa/", mpesa_callback, name="mpesa-callback"),
]
