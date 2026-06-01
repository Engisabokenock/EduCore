"""
Academic views — REST API Design (Step 4).

Endpoints:
    GET     /api/v1/academic/grades/                    List all grades
    GET     /api/v1/academic/grades/{slug}/             Grade detail + subjects
    POST    /api/v1/academic/grades/                    Create grade (admin)
    PUT     /api/v1/academic/grades/{slug}/             Update grade (admin)
    DELETE  /api/v1/academic/grades/{slug}/             Delete grade (admin)

    GET     /api/v1/academic/subjects/                  List subjects (filterable by grade)
    GET     /api/v1/academic/subjects/{slug}/           Subject detail + topics
    POST    /api/v1/academic/subjects/                  Create (admin)
    ...

    GET     /api/v1/academic/topics/                    List topics (filterable by subject)
    GET     /api/v1/academic/topics/{slug}/             Topic detail
    POST    /api/v1/academic/topics/                    Create (admin)
    ...

    GET     /api/v1/academic/enrollments/               My enrollments
    POST    /api/v1/academic/enrollments/               Enroll in a grade

Filtering:
    GET /api/v1/academic/subjects/?grade=grade-5
    GET /api/v1/academic/topics/?subject=mathematics
    GET /api/v1/academic/resources/?grade=grade-5&subject=mathematics
"""
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet, GenericViewSet
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from django_filters.rest_framework import DjangoFilterBackend

from core.pagination import StandardResultsPagination
from core.permissions import IsAdminOrReadOnly
from core.responses import success_response, created_response, error_response
from . import services
from .filters import GradeFilterSet, SubjectFilterSet, TopicFilterSet
from .models import Grade, Subject, Topic, Enrollment
from .serializers import (
    GradeListSerializer, GradeDetailSerializer, GradeWriteSerializer,
    SubjectListSerializer, SubjectDetailSerializer, SubjectWriteSerializer,
    TopicListSerializer, TopicDetailSerializer, TopicWriteSerializer,
    EnrollmentSerializer,
)


class GradeViewSet(ModelViewSet):
    """
    GET     /grades/          List all active grades
    GET     /grades/{slug}/   Grade detail (with subject count)
    POST    /grades/          Create grade (admin only)
    PUT     /grades/{slug}/   Update grade (admin only)
    DELETE  /grades/{slug}/   Delete grade (admin only)
    """
    lookup_field = "slug"
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = GradeFilterSet
    search_fields = ["name", "code"]
    ordering_fields = ["order", "name", "curriculum"]
    ordering = ["order"]

    def get_queryset(self):
        return Grade.objects.prefetch_related("subjects").order_by("order")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return GradeWriteSerializer
        if self.action == "retrieve":
            return GradeDetailSerializer
        return GradeListSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminOrReadOnly()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(data=self.get_serializer(queryset, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return success_response(data=self.get_serializer(instance).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        grade = serializer.save()
        return created_response(
            data=GradeDetailSerializer(grade).data,
            message="Grade created successfully.",
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        grade = serializer.save()
        return success_response(
            data=GradeDetailSerializer(grade).data,
            message="Grade updated successfully.",
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        instance.delete()
        return success_response(message=f"Grade '{name}' deleted.")

    @action(detail=True, methods=["get"], url_path="subjects")
    def subjects(self, request, slug=None):
        """GET /grades/{slug}/subjects/ — subjects within a specific grade."""
        grade = self.get_object()
        subjects = grade.subjects.filter(is_active=True).order_by("order")
        subjects = SubjectListSerializer(subjects, many=True).data
        return success_response(data=subjects)


class SubjectViewSet(ModelViewSet):
    """
    GET     /subjects/          List subjects (filterable by ?grade=<slug>)
    GET     /subjects/{slug}/   Subject detail with topic count
    POST    /subjects/          Create (admin)
    PUT     /subjects/{slug}/   Update (admin)
    DELETE  /subjects/{slug}/   Delete (admin)
    GET     /subjects/{slug}/topics/  Topics in a subject
    """
    lookup_field = "slug"
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SubjectFilterSet
    search_fields = ["name", "description"]
    ordering_fields = ["order", "name"]
    ordering = ["order"]

    def get_queryset(self):
        return Subject.objects.select_related("grade").prefetch_related("topics").order_by("grade__order", "order")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return SubjectWriteSerializer
        if self.action == "retrieve":
            return SubjectDetailSerializer
        return SubjectListSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve", "topics"):
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminOrReadOnly()]

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
        subject = serializer.save()
        return created_response(
            data=SubjectDetailSerializer(subject, context={"request": request}).data,
            message="Subject created successfully.",
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        subject = serializer.save()
        return success_response(
            data=SubjectDetailSerializer(subject, context={"request": request}).data,
            message="Subject updated successfully.",
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        instance.delete()
        return success_response(message=f"Subject '{name}' deleted.")

    @action(detail=True, methods=["get"], url_path="topics", permission_classes=[AllowAny])
    def topics(self, request, slug=None):
        """GET /subjects/{slug}/topics/ — topics within a specific subject."""
        subject = self.get_object()
        qs = subject.topics.filter(is_active=True).order_by("order")
        return success_response(data=TopicListSerializer(qs, many=True).data)


class TopicViewSet(ModelViewSet):
    """
    GET     /topics/          List topics (filterable by ?subject=<slug>)
    GET     /topics/{slug}/   Topic detail
    POST    /topics/          Create (admin)
    PUT     /topics/{slug}/   Update (admin)
    DELETE  /topics/{slug}/   Delete (admin)
    GET     /topics/{slug}/resources/ Resources for this topic
    """
    lookup_field = "slug"
    pagination_class = StandardResultsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TopicFilterSet
    search_fields = ["name", "description"]
    ordering_fields = ["order", "name"]
    ordering = ["order"]

    def get_queryset(self):
        return Topic.objects.select_related("subject__grade").order_by("subject__order", "order")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return TopicWriteSerializer
        if self.action == "retrieve":
            return TopicDetailSerializer
        return TopicListSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve", "resources"):
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminOrReadOnly()]

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
        topic = serializer.save()
        return created_response(
            data=TopicDetailSerializer(topic, context={"request": request}).data,
            message="Topic created successfully.",
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        topic = serializer.save()
        return success_response(
            data=TopicDetailSerializer(topic, context={"request": request}).data,
            message="Topic updated successfully.",
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        instance.delete()
        return success_response(message=f"Topic '{name}' deleted.")

    @action(detail=True, methods=["get"], url_path="resources", permission_classes=[AllowAny])
    def resources(self, request, slug=None):
        """GET /topics/{slug}/resources/ — published resources for this topic."""
        topic = self.get_object()
        from apps.content.models import Resource
        from apps.content.serializers import ResourceListSerializer
        qs = Resource.objects.filter(topic=topic, is_published=True).select_related("grade", "subject")
        serializer = ResourceListSerializer(qs, many=True)
        return success_response(data=serializer.data)


class EnrollmentViewSet(ListModelMixin, CreateModelMixin, GenericViewSet):
    """
    GET     /enrollments/  — current user's enrollments
    POST    /enrollments/  — enroll in a grade
    """
    permission_classes = [IsAuthenticated]
    serializer_class = EnrollmentSerializer
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user).select_related("grade")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(data=self.get_serializer(queryset, many=True).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enrollment = serializer.save()
        return created_response(
            data=EnrollmentSerializer(enrollment).data,
            message=f"Enrolled in {enrollment.grade.name} successfully.",
        )
