"""
Search views.

GET /api/v1/search/?q=algebra
GET /api/v1/search/?q=grade+5+math&category=resources
GET /api/v1/search/?q=fractions&category=topics
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.db.models import Q

from core.responses import success_response, error_response
from apps.content.models import Resource
from apps.content.serializers import ResourceListSerializer
from apps.academic.models import Grade, Subject, Topic
from apps.academic.serializers import GradeListSerializer, SubjectListSerializer, TopicListSerializer

_RESOURCE_LIMIT = 12
_GRADE_LIMIT = 5
_SUBJECT_LIMIT = 8
_TOPIC_LIMIT = 8


def _tags_q(query: str) -> Q:
    """
    PostgreSQL JSONField array tag search.
    Django 4.x: `tags__icontains` casts the JSONField to text and does ILIKE,
    which correctly matches any tag whose value contains the substring.
    We also try an exact-element match via `tags__contains` for clean single-word
    queries so ranked results surface exact-tag hits first.
    """
    q = Q(tags__icontains=query)
    # Exact element match (e.g. query="algebra" matches tag "algebra" precisely)
    try:
        q |= Q(tags__contains=[query.lower()])
    except Exception:
        pass
    return q


@api_view(["GET"])
@permission_classes([AllowAny])
def search(request):
    """
    GET /api/v1/search/?q=<query>[&category=all|resources|grades|subjects|topics]

    Returns:
    {
        "success": true,
        "data": {
            "query": "algebra",
            "resources": [...],
            "grades": [...],
            "subjects": [...],
            "topics": [...]
        },
        "meta": {"total": <int>}
    }
    """
    query = request.query_params.get("q", "").strip()
    category = request.query_params.get("category", "all").lower()

    if not query:
        return error_response("Query parameter 'q' is required.", status_code=400)
    if len(query) < 2:
        return error_response("Query must be at least 2 characters.", status_code=400)
    if category not in ("all", "resources", "grades", "subjects", "topics"):
        return error_response("Invalid category. Use: all, resources, grades, subjects, topics.", status_code=400)

    results: dict = {}
    total = 0

    if category in ("all", "resources"):
        qs = (
            Resource.objects.filter(is_published=True)
            .filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | _tags_q(query)
            )
            .select_related("grade", "subject", "topic")
            .order_by("-download_count")[:_RESOURCE_LIMIT]
        )
        results["resources"] = ResourceListSerializer(qs, many=True, context={"request": request}).data
        total += len(results["resources"])

    if category in ("all", "grades"):
        qs = (
            Grade.objects.filter(is_active=True)
            .filter(Q(name__icontains=query) | Q(code__icontains=query))
            .order_by("order")[:_GRADE_LIMIT]
        )
        results["grades"] = GradeListSerializer(qs, many=True).data
        total += len(results["grades"])

    if category in ("all", "subjects"):
        qs = (
            Subject.objects.filter(is_active=True)
            .filter(Q(name__icontains=query) | Q(description__icontains=query))
            .select_related("grade")
            .order_by("grade__order", "order")[:_SUBJECT_LIMIT]
        )
        results["subjects"] = SubjectListSerializer(qs, many=True).data
        total += len(results["subjects"])

    if category in ("all", "topics"):
        qs = (
            Topic.objects.filter(is_active=True)
            .filter(Q(name__icontains=query) | Q(description__icontains=query))
            .select_related("subject__grade")
            .order_by("subject__grade__order", "subject__order", "order")[:_TOPIC_LIMIT]
        )
        results["topics"] = TopicListSerializer(qs, many=True).data
        total += len(results["topics"])

    return success_response(
        data={"query": query, "category": category, **results},
        meta={"total": total},
    )

