"""Community views — Reviews with REST ViewSet."""
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from django.db.models import Avg, Count
from django_filters.rest_framework import DjangoFilterBackend
import django_filters

from core.pagination import StandardResultsPagination
from core.responses import success_response, created_response, error_response
from .models import Review
from .serializers import ReviewSerializer


class ReviewFilterSet(django_filters.FilterSet):
    resource = django_filters.UUIDFilter(field_name="resource__id")
    resource_slug = django_filters.CharFilter(field_name="resource__slug")
    rating = django_filters.NumberFilter()
    rating_min = django_filters.NumberFilter(field_name="rating", lookup_expr="gte")
    rating_max = django_filters.NumberFilter(field_name="rating", lookup_expr="lte")

    class Meta:
        model = Review
        fields = ["resource", "resource_slug", "rating"]


class ReviewViewSet(ModelViewSet):
    """
    GET    /reviews/           List approved reviews (filterable by ?resource_slug=)
    POST   /reviews/           Create a review (authenticated)
    GET    /reviews/{id}/      Review detail
    PUT    /reviews/{id}/      Update own review
    PATCH  /reviews/{id}/      Partial update
    DELETE /reviews/{id}/      Delete own review
    GET    /reviews/mine/      My reviews
    GET    /reviews/stats/     Aggregate ratings for a resource (?resource_slug=)
    """
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = ReviewFilterSet
    ordering_fields = ["rating", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if self.action == "mine":
            return Review.objects.filter(user=self.request.user).select_related("resource")
        return Review.objects.filter(is_approved=True).select_related("user", "resource")

    def get_serializer_class(self):
        return ReviewSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve", "stats"):
            return [AllowAny()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(data=self.get_serializer(queryset, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        return success_response(data=self.get_serializer(self.get_object()).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Prevent duplicate reviews
        if Review.objects.filter(user=request.user, resource_id=request.data.get("resource")).exists():
            return error_response("You have already reviewed this resource.", status_code=400)
        review = serializer.save(user=request.user)
        return created_response(
            data=self.get_serializer(review).data,
            message="Review submitted successfully.",
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        if instance.user != request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only edit your own reviews.")
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return success_response(data=self.get_serializer(review).data, message="Review updated.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user and request.user.role != "admin":
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own reviews.")
        instance.delete()
        return success_response(message="Review deleted.")

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def mine(self, request):
        """GET /reviews/mine/ — current user's reviews."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(data=self.get_serializer(queryset, many=True).data)

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def stats(self, request):
        """GET /reviews/stats/?resource_slug=<slug> — average rating + count."""
        resource_slug = request.query_params.get("resource_slug")
        if not resource_slug:
            return error_response("resource_slug query parameter is required.", status_code=400)
        agg = Review.objects.filter(
            resource__slug=resource_slug, is_approved=True
        ).aggregate(
            average_rating=Avg("rating"),
            review_count=Count("id"),
        )
        return success_response(
            data={
                "resource_slug": resource_slug,
                "average_rating": round(agg["average_rating"] or 0, 1),
                "review_count": agg["review_count"],
            }
        )
