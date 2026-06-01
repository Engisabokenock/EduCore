from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

from core.permissions import IsAdmin
from .models import Event, DailyStats
from . import services


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def track(request):
    event_type = request.data.get("event_type")
    data = request.data.get("data", {})
    if event_type:
        services.track_event(event_type, user=request.user, data=data, request=request)
    return Response({"status": "ok"})


@api_view(["GET"])
@permission_classes([IsAdmin])
def dashboard_stats(request):
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    downloads_30d = Event.objects.filter(
        event_type=Event.EventType.RESOURCE_DOWNLOAD,
        timestamp__date__gte=thirty_days_ago,
    ).count()

    top_resources = (
        Event.objects.filter(event_type=Event.EventType.RESOURCE_VIEW)
        .values("data__resource_id", "data__resource_title")
        .annotate(views=Count("id"))
        .order_by("-views")[:10]
    )

    return Response(
        {
            "downloads_last_30_days": downloads_30d,
            "top_resources": list(top_resources),
        }
    )
