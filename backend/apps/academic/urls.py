"""
Academic URL routing via DRF Router.

    GET  /api/v1/academic/grades/                   List grades
    GET  /api/v1/academic/grades/{slug}/            Grade detail
    GET  /api/v1/academic/grades/{slug}/subjects/   Subjects in grade
    POST /api/v1/academic/grades/                   Create grade (admin)
    PUT  /api/v1/academic/grades/{slug}/            Update grade (admin)
    DEL  /api/v1/academic/grades/{slug}/            Delete grade (admin)

    GET  /api/v1/academic/subjects/                 List subjects (?grade=slug)
    GET  /api/v1/academic/subjects/{slug}/          Subject detail
    GET  /api/v1/academic/subjects/{slug}/topics/   Topics in subject
    POST /api/v1/academic/subjects/                 Create subject (admin)
    ...

    GET  /api/v1/academic/topics/                   List topics (?subject=slug)
    GET  /api/v1/academic/topics/{slug}/            Topic detail
    GET  /api/v1/academic/topics/{slug}/resources/  Resources for topic
    POST /api/v1/academic/topics/                   Create topic (admin)
    ...

    GET  /api/v1/academic/enrollments/              My enrollments
    POST /api/v1/academic/enrollments/              Enroll
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GradeViewSet, SubjectViewSet, TopicViewSet, EnrollmentViewSet

router = DefaultRouter()
router.register(r"grades", GradeViewSet, basename="grade")
router.register(r"subjects", SubjectViewSet, basename="subject")
router.register(r"topics", TopicViewSet, basename="topic")
router.register(r"enrollments", EnrollmentViewSet, basename="enrollment")

app_name = "academic"

urlpatterns = [
    path("", include(router.urls)),
]
