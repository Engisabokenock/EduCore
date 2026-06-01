"""Media app models: MediaFile management."""
import uuid
from django.db import models

from core.models import BaseModel


class MediaFile(BaseModel):
    """Uploaded media file."""

    class FileType(models.TextChoices):
        IMAGE = "image", "Image"
        PDF = "pdf", "PDF"
        VIDEO = "video", "Video"
        AUDIO = "audio", "Audio"
        DOCUMENT = "document", "Document"
        OTHER = "other", "Other"

    user = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="media_files"
    )
    file = models.FileField(upload_to="media/%Y/%m/")
    original_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FileType.choices, default=FileType.OTHER)
    mime_type = models.CharField(max_length=100, blank=True)
    size = models.PositiveIntegerField(default=0, help_text="File size in bytes")
    width = models.PositiveIntegerField(null=True, blank=True, help_text="For images/videos")
    height = models.PositiveIntegerField(null=True, blank=True)
    duration = models.PositiveIntegerField(null=True, blank=True, help_text="Duration in seconds for audio/video")
    is_public = models.BooleanField(default=False)
    cdn_url = models.URLField(blank=True, help_text="CDN URL if synced to cloud storage")

    class Meta:
        db_table = "media_files"
        ordering = ["-created_at"]

    def __str__(self):
        return self.original_name

    @property
    def url(self):
        return self.cdn_url or (self.file.url if self.file else "")

    @property
    def size_mb(self):
        return round(self.size / (1024 * 1024), 2)
