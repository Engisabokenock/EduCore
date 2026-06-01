from django.urls import path
from . import views

urlpatterns = [
    path("track/", views.track, name="analytics-track"),
    path("dashboard/", views.dashboard_stats, name="analytics-dashboard"),
]
