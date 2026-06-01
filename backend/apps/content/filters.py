"""
Resource FilterSet.

Supports:
    GET /api/v1/resources/?grade=grade-5
    GET /api/v1/resources/?subject=mathematics
    GET /api/v1/resources/?topic=fractions
    GET /api/v1/resources/?term=1
    GET /api/v1/resources/?year=2023
    GET /api/v1/resources/?type=past_paper
    GET /api/v1/resources/?is_premium=false
    GET /api/v1/resources/?search=algebra
    GET /api/v1/resources/?ordering=-download_count
    GET /api/v1/resources/?grade=grade-5&subject=mathematics&type=past_paper
"""
import django_filters
from .models import Resource


class ResourceFilterSet(django_filters.FilterSet):
    # Filter by grade slug (e.g. ?grade=grade-5)
    grade = django_filters.CharFilter(field_name="grade__slug", lookup_expr="iexact")
    # Filter by grade id (e.g. ?grade_id=<uuid>)
    grade_id = django_filters.UUIDFilter(field_name="grade__id")

    # Filter by subject slug (e.g. ?subject=mathematics)
    subject = django_filters.CharFilter(field_name="subject__slug", lookup_expr="iexact")
    subject_id = django_filters.UUIDFilter(field_name="subject__id")

    # Filter by topic slug (e.g. ?topic=fractions)
    topic = django_filters.CharFilter(field_name="topic__slug", lookup_expr="iexact")
    topic_id = django_filters.UUIDFilter(field_name="topic__id")

    # Academic metadata filters
    term = django_filters.NumberFilter(field_name="term")
    year = django_filters.NumberFilter(field_name="year")
    year_min = django_filters.NumberFilter(field_name="year", lookup_expr="gte")
    year_max = django_filters.NumberFilter(field_name="year", lookup_expr="lte")

    # Resource type (e.g. ?type=past_paper)
    type = django_filters.CharFilter(field_name="resource_type", lookup_expr="iexact")

    # Access filter
    is_premium = django_filters.BooleanFilter(field_name="is_premium")

    # Curriculum (CBC, 8-4-4, IGCSE)
    curriculum = django_filters.CharFilter(field_name="grade__curriculum", lookup_expr="iexact")

    # Tag filter (checks if tag exists in JSON array)
    tag = django_filters.CharFilter(method="filter_by_tag")

    class Meta:
        model = Resource
        fields = [
            "grade", "grade_id", "subject", "subject_id",
            "topic", "topic_id", "term", "year", "type",
            "is_premium", "curriculum", "tag",
        ]

    def filter_by_tag(self, queryset, name, value):
        return queryset.filter(tags__contains=[value])
