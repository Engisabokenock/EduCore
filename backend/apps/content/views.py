"""
Content views — REST API Design (Step 4).

Endpoints:
    GET     /api/v1/resources/                      List resources (filterable, paginated)
    POST    /api/v1/resources/                      Create resource (teacher/admin)
    GET     /api/v1/resources/{slug}/               Resource detail
    PUT     /api/v1/resources/{slug}/               Full update (teacher/admin, own resource)
    PATCH   /api/v1/resources/{slug}/               Partial update
    DELETE  /api/v1/resources/{slug}/               Delete (admin only)
    POST    /api/v1/resources/{slug}/download/      Download a resource (returns file URL)
    GET     /api/v1/resources/downloads/mine/       My download history

Filtering (GET /api/v1/resources/):
    ?grade=grade-5
    ?subject=mathematics
    ?topic=fractions
    ?term=1
    ?year=2023
    ?type=past_paper
    ?is_premium=false
    ?search=algebra
    ?ordering=-download_count,-created_at

HTTP method → action mapping:
    GET    → list / retrieve   (safe, read-only)
    POST   → create
    PUT    → update (full replace)
    PATCH  → partial_update
    DELETE → destroy
"""
from django.shortcuts import get_object_or_404
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from core.pagination import StandardResultsPagination
from core.performance import optimize_content_queryset
from core.permissions import IsTeacherOrReadOnly, IsAdmin
from core.responses import (
    success_response, created_response, not_found_response,
    forbidden_response, error_response,
)
from . import services
from .filters import ResourceFilterSet
from .models import Resource, Download
from .serializers import (
    ResourceListSerializer,
    ResourceDetailSerializer,
    ResourceWriteSerializer,
    DownloadSerializer,
)


def _require_premium(user, resource=None):
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "role", None) == "admin":
        return True
    if resource and not resource.is_premium:
        return True
    return user.subscriptions.filter(status="active").exists()


class ResourceViewSet(ModelViewSet):
    """
    Full CRUD ViewSet for Resource.

    GET     /resources/           → list
    POST    /resources/           → create
    GET     /resources/{slug}/    → retrieve
    PUT     /resources/{slug}/    → update
    PATCH   /resources/{slug}/    → partial_update
    DELETE  /resources/{slug}/    → destroy
    """

    lookup_field = "slug"
    pagination_class = StandardResultsPagination

    # Filtering
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ResourceFilterSet
    search_fields = ["title", "description", "tags"]
    ordering_fields = ["created_at", "view_count", "download_count", "title", "year"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if self.action in ("list", "retrieve", "download"):
            return services.get_published_resources()
        # Teachers/admins can see their own unpublished resources
        user = self.request.user
        if user.is_authenticated and user.role == "admin":
            return Resource.objects.select_related("grade", "subject", "topic").all()
        if user.is_authenticated and user.role == "teacher":
            return Resource.objects.filter(author=user).select_related("grade", "subject", "topic")
        return services.get_published_resources()

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ResourceWriteSerializer
        if self.action == "retrieve":
            return ResourceDetailSerializer
        return ResourceListSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        if self.action == "destroy":
            return [IsAuthenticated(), IsAdmin()]
        if self.action in ("create", "update", "partial_update"):
            return [IsAuthenticated(), IsTeacherOrReadOnly()]
        return [IsAuthenticated()]

    # ── LIST: GET /resources/ ─────────────────────────────────────────────────
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    # ── RETRIEVE: GET /resources/{slug}/ ─────────────────────────────────────
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        services.record_view(instance)
        serializer = self.get_serializer(instance)
        return success_response(data=serializer.data)

    # ── CREATE: POST /resources/ ──────────────────────────────────────────────
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resource = serializer.save()
        return created_response(
            data=ResourceDetailSerializer(resource, context={"request": request}).data,
            message="Resource created successfully.",
        )

    # ── UPDATE: PUT /resources/{slug}/ ───────────────────────────────────────
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        self._check_ownership(request, instance)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        resource = serializer.save()
        return success_response(
            data=ResourceDetailSerializer(resource, context={"request": request}).data,
            message="Resource updated successfully.",
        )

    # ── DELETE: DELETE /resources/{slug}/ ────────────────────────────────────
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        title = instance.title
        instance.delete()
        return success_response(message=f"'{title}' deleted successfully.")

    # ── DOWNLOAD: POST /resources/{slug}/download/ ────────────────────────────
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated], url_path="download")
    def download(self, request, slug=None):
        resource = self.get_object()

        if not _require_premium(request.user, resource):
            return forbidden_response(
                "This resource requires a Premium subscription. "
                "Upgrade at /pricing to unlock all content."
            )

        services.record_download(
            resource,
            user=request.user,
            ip_address=services.get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )

        if resource.pdf_file:
            file_url = services.get_signed_file_url(request, request.build_absolute_uri(resource.pdf_file.url))
            if not file_url:
                return error_response("Unable to generate download link.", status_code=403)
        elif resource.external_url:
            file_url = resource.external_url
        else:
            return error_response("No file available for this resource.", status_code=404)

        return success_response(
            data={
                "file_url": file_url,
                "filename": resource.title,
                "file_type": resource.file_type,
                "file_size": resource.file_size,
            },
            message="Download ready.",
        )

    # ── ANSWER SHEET: GET /resources/{slug}/answer-sheet/ ────────────────────
    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated], url_path="answer-sheet")
    def answer_sheet(self, request, slug=None):
        resource = self.get_object()

        if not resource.has_answer_sheet:
            return error_response("No answer sheet available for this resource.", status_code=404)

        if not _require_premium(request.user, resource):
            return forbidden_response("Answer sheets require a Premium subscription.")

        raw_url = request.build_absolute_uri(resource.answer_sheet.url)
        signed_url = services.get_signed_file_url(request, raw_url)
        file_url = signed_url or raw_url

        return success_response(
            data={"answer_sheet_url": file_url, "filename": f"{resource.title} — Answer Sheet"},
            message="Answer sheet ready.",
        )

    # ── PUBLISH: POST /resources/{slug}/publish/ (admin/teacher) ─────────────
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsTeacherOrReadOnly], url_path="publish")
    def publish(self, request, slug=None):
        resource = self.get_object()
        self._check_ownership(request, resource)
        services.publish_resource(resource)
        return success_response(message=f"'{resource.title}' is now published.")

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsTeacherOrReadOnly], url_path="unpublish")
    def unpublish(self, request, slug=None):
        resource = self.get_object()
        self._check_ownership(request, resource)
        services.unpublish_resource(resource)
        return success_response(message=f"'{resource.title}' unpublished.")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _check_ownership(self, request, resource: Resource):
        """Raises PermissionDenied if non-admin tries to edit someone else's resource."""
        if request.user.role != "admin" and resource.author != request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only modify your own resources.")


class MyDownloadsViewSet(ReadOnlyModelViewSet):
    """
    GET /api/v1/resources/downloads/        — list user's download history
    GET /api/v1/resources/downloads/{id}/   — detail
    """
    permission_classes = [IsAuthenticated]
    serializer_class = DownloadSerializer
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        return Download.objects.filter(user=self.request.user).select_related(
            "resource__grade", "resource__subject", "resource__topic"
        ).order_by("-downloaded_at")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)
