"""
Content URL routing.

Uses DRF Router for clean REST URL generation:

    GET     /api/v1/resources/                      List (filterable, paginated)
    POST    /api/v1/resources/                      Create
    GET     /api/v1/resources/{slug}/               Detail
    PUT     /api/v1/resources/{slug}/               Update
    PATCH   /api/v1/resources/{slug}/               Partial update
    DELETE  /api/v1/resources/{slug}/               Delete
    POST    /api/v1/resources/{slug}/download/      Download file
    GET     /api/v1/resources/{slug}/answer-sheet/  Answer sheet
    POST    /api/v1/resources/{slug}/publish/       Publish
    POST    /api/v1/resources/{slug}/unpublish/     Unpublish
    GET     /api/v1/resources/downloads/            My download history
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResourceViewSet, MyDownloadsViewSet

router = DefaultRouter()
router.register(r"", ResourceViewSet, basename="resource")
router.register(r"downloads", MyDownloadsViewSet, basename="download")

urlpatterns = [
    path("", include(router.urls)),
]
