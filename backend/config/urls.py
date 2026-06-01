"""
Main URL configuration for EduCore Platform.

API Base URL: /api/v1/

Endpoints:
  /api/v1/auth/               Authentication (JWT)
  /api/v1/academic/           Grade → Subject → Topic hierarchy
  /api/v1/resources/          Learning resources (notes, past papers, etc.)
  /api/v1/commerce/           Plans, subscriptions, M-Pesa payments
  /api/v1/reviews/            Resource reviews and ratings
  /api/v1/search/             Full-text search
  /api/v1/analytics/          Event tracking and stats
  /api/v1/notifications/      User notifications
  /api/v1/media/              File uploads

System:
  /health/                    Health check
  /readiness/                 DB readiness probe
  /liveness/                  Process liveness probe
  /admin/                     Django admin
  /api/v1/docs/               Swagger UI
  /api/v1/redoc/              ReDoc
"""
from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


def health_check(request):
    return JsonResponse(
        {
            "success": True,
            "status": "healthy",
            "service": "educore-api",
            "version": settings.API_VERSION,
            "environment": "development" if settings.DEBUG else "production",
        }
    )


def readiness_check(request):
    from django.db import connection
    try:
        connection.ensure_connection()
        return JsonResponse({"success": True, "status": "ready"})
    except Exception:
        return JsonResponse(
            {"success": False, "status": "not_ready"}, status=503
        )


def liveness_check(request):
    return JsonResponse({"success": True, "status": "alive"})


# ── API v1 routes ─────────────────────────────────────────────────────────────
api_v1_patterns = [
    path("auth/", include("apps.accounts.urls")),
    path("academic/", include("apps.academic.urls")),
    path("resources/", include("apps.content.urls")),
    path("commerce/", include("apps.commerce.urls")),
    path("reviews/", include("apps.community.urls")),
    path("search/", include("apps.search.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("media/", include("apps.media.urls")),
]

# ── Root urlpatterns ──────────────────────────────────────────────────────────
urlpatterns = [
    path("admin/", admin.site.urls),
    # System endpoints
    path("health/", health_check, name="health_check"),
    path("readiness/", readiness_check, name="readiness_check"),
    path("liveness/", liveness_check, name="liveness_check"),
    # API v1
    path(f"{settings.API_URL_PREFIX}/", include(api_v1_patterns)),
    # API documentation (OpenAPI)
    path(f"{settings.API_URL_PREFIX}/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        f"{settings.API_URL_PREFIX}/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        f"{settings.API_URL_PREFIX}/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
