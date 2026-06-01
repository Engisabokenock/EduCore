"""
Academic FilterSets.
"""
import django_filters
from .models import Grade, Subject, Topic


class GradeFilterSet(django_filters.FilterSet):
    curriculum = django_filters.CharFilter(lookup_expr="iexact")
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Grade
        fields = ["curriculum", "is_active"]


class SubjectFilterSet(django_filters.FilterSet):
    grade = django_filters.CharFilter(field_name="grade__slug", lookup_expr="iexact")
    grade_id = django_filters.UUIDFilter(field_name="grade__id")
    curriculum = django_filters.CharFilter(field_name="grade__curriculum", lookup_expr="iexact")
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Subject
        fields = ["grade", "grade_id", "curriculum", "is_active"]


class TopicFilterSet(django_filters.FilterSet):
    subject = django_filters.CharFilter(field_name="subject__slug", lookup_expr="iexact")
    subject_id = django_filters.UUIDFilter(field_name="subject__id")
    grade = django_filters.CharFilter(field_name="subject__grade__slug", lookup_expr="iexact")
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Topic
        fields = ["subject", "subject_id", "grade", "is_active"]
