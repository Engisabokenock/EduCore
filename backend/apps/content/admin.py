from django.contrib import admin
from django.utils import timezone
from .models import Resource, Download


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = [
        "title", "resource_type", "grade", "subject", "topic",
        "term", "year", "is_premium", "has_answer_sheet",
        "is_published", "view_count", "download_count",
    ]
    list_filter = [
        "resource_type", "is_premium", "is_published",
        "term", "grade__curriculum", "grade",
    ]
    search_fields = ["title", "description", "slug"]
    list_editable = ["is_published", "is_premium"]
    raw_id_fields = ["grade", "subject", "topic", "author"]
    readonly_fields = ["slug", "view_count", "download_count", "created_at", "updated_at"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        ("Content", {
            "fields": ("title", "slug", "description", "resource_type", "tags"),
        }),
        ("Academic Placement", {
            "fields": ("grade", "subject", "topic", "term", "year"),
        }),
        ("Files", {
            "fields": ("pdf_file", "answer_sheet", "thumbnail", "external_url", "file_type", "file_size"),
        }),
        ("Access & Publishing", {
            "fields": ("is_premium", "is_published", "published_at", "author"),
        }),
        ("Stats (read-only)", {
            "classes": ("collapse",),
            "fields": ("view_count", "download_count", "created_at", "updated_at"),
        }),
    )

    actions = ["publish_selected", "unpublish_selected", "make_premium", "make_free"]

    def has_answer_sheet(self, obj):
        return bool(obj.answer_sheet)
    has_answer_sheet.boolean = True
    has_answer_sheet.short_description = "Answer Sheet"

    def publish_selected(self, request, queryset):
        queryset.update(is_published=True, published_at=timezone.now())
        self.message_user(request, f"{queryset.count()} resource(s) published.")
    publish_selected.short_description = "Publish selected resources"

    def unpublish_selected(self, request, queryset):
        queryset.update(is_published=False)
        self.message_user(request, f"{queryset.count()} resource(s) unpublished.")
    unpublish_selected.short_description = "Unpublish selected resources"

    def make_premium(self, request, queryset):
        queryset.update(is_premium=True)
        self.message_user(request, f"{queryset.count()} resource(s) set to premium.")
    make_premium.short_description = "Mark selected as Premium"

    def make_free(self, request, queryset):
        queryset.update(is_premium=False)
        self.message_user(request, f"{queryset.count()} resource(s) set to free.")
    make_free.short_description = "Mark selected as Free"


@admin.register(Download)
class DownloadAdmin(admin.ModelAdmin):
    list_display = ["resource", "user", "ip_address", "downloaded_at"]
    list_filter = ["downloaded_at"]
    search_fields = ["resource__title", "user__email", "ip_address"]
    raw_id_fields = ["user", "resource"]
    readonly_fields = ["downloaded_at"]
    date_hierarchy = "downloaded_at"
