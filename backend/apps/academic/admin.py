from django.contrib import admin
from .models import Grade, Subject, Topic, Enrollment


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "curriculum", "order", "is_active"]
    list_filter = ["curriculum", "is_active"]
    search_fields = ["name", "code"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["order"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "grade", "order", "is_active"]
    list_filter = ["grade__curriculum", "is_active", "grade"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["grade__order", "order"]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["name", "subject", "order", "is_active"]
    list_filter = ["subject__grade", "is_active"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["subject__order", "order"]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["user", "grade", "status", "enrolled_at"]
    list_filter = ["status", "grade__curriculum"]
    search_fields = ["user__email", "grade__name"]
    raw_id_fields = ["user"]
