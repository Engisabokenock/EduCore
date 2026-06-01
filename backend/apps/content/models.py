"""
Content app models.

Data Model (Step 3):
    Grade → Subject → Topic → Resource

Resource fields per spec:
    title, description, grade, subject, topic, term,
    pdf_file, answer_sheet, is_premium, download_count
"""
import uuid
from django.db import models
from django.utils.text import slugify

from core.models import BaseModel


class Resource(BaseModel):
    """A learning resource: note, past paper, worksheet, revision guide, or video."""

    class ResourceType(models.TextChoices):
        NOTES = "notes", "Notes"
        PAST_PAPER = "past_paper", "Past Paper"
        WORKSHEET = "worksheet", "Worksheet"
        REVISION = "revision", "Revision Guide"
        VIDEO = "video", "Video Lesson"
        AUDIO = "audio", "Audio Lesson"
        EBOOK = "ebook", "eBook"

    class Term(models.IntegerChoices):
        TERM_1 = 1, "Term 1"
        TERM_2 = 2, "Term 2"
        TERM_3 = 3, "Term 3"

    # ── Core identity ────────────────────────────────────────────────────────
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=350, unique=True, blank=True, db_index=True)
    description = models.TextField(blank=True)
    resource_type = models.CharField(
        max_length=20, choices=ResourceType.choices, db_index=True
    )

    # ── Academic placement (Grade → Subject → Topic) ─────────────────────────
    grade = models.ForeignKey(
        "academic.Grade",
        on_delete=models.PROTECT,
        related_name="resources",
        db_index=True,
    )
    subject = models.ForeignKey(
        "academic.Subject",
        on_delete=models.PROTECT,
        related_name="resources",
        db_index=True,
    )
    topic = models.ForeignKey(
        "academic.Topic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resources",
    )

    # ── Academic metadata ────────────────────────────────────────────────────
    term = models.IntegerField(choices=Term.choices, null=True, blank=True, db_index=True)
    year = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="Exam year, e.g. 2023 (for past papers)"
    )
    tags = models.JSONField(default=list, blank=True)

    # ── Files ────────────────────────────────────────────────────────────────
    pdf_file = models.FileField(
        upload_to="resources/pdfs/%Y/%m/",
        null=True,
        blank=True,
        help_text="Primary resource file (PDF, DOCX, etc.)",
    )
    answer_sheet = models.FileField(
        upload_to="resources/answers/%Y/%m/",
        null=True,
        blank=True,
        help_text="Answer sheet / marking scheme (optional)",
    )
    thumbnail = models.ImageField(upload_to="resources/thumbnails/", null=True, blank=True)
    external_url = models.URLField(blank=True, help_text="YouTube / Vimeo / external link")

    # File metadata (auto-populated)
    file_size = models.PositiveIntegerField(default=0, help_text="Primary file size in bytes")
    file_type = models.CharField(max_length=10, blank=True, help_text="e.g. pdf, mp4")

    # ── Access control ───────────────────────────────────────────────────────
    is_premium = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Requires active subscription to download",
    )

    # ── Authorship ───────────────────────────────────────────────────────────
    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authored_resources",
    )

    # ── Stats ────────────────────────────────────────────────────────────────
    view_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)

    # ── Publishing ───────────────────────────────────────────────────────────
    is_published = models.BooleanField(default=False, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "content_resources"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["grade", "subject", "topic"]),
            models.Index(fields=["resource_type", "is_premium", "is_published"]),
            models.Index(fields=["term", "year"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.db import transaction as db_transaction
            base = slugify(self.title) or "resource"
            # Use select_for_update inside atomic to prevent concurrent duplicates
            with db_transaction.atomic():
                slug = base
                n = 1
                while Resource.objects.select_for_update().filter(slug=slug).exclude(pk=self.pk).exists():
                    slug = f"{base}-{n}"
                    n += 1
                self.slug = slug
        super().save(*args, **kwargs)

    # ── Computed helpers ──────────────────────────────────────────────────────
    @property
    def is_free(self) -> bool:
        return not self.is_premium

    @property
    def has_answer_sheet(self) -> bool:
        return bool(self.answer_sheet)


class Download(BaseModel):
    """Tracks every download event for analytics and access gating."""

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="downloads",
    )
    resource = models.ForeignKey(
        Resource, on_delete=models.CASCADE, related_name="download_logs"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    downloaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "content_downloads"
        ordering = ["-downloaded_at"]
        indexes = [
            models.Index(fields=["user", "resource"]),
            models.Index(fields=["downloaded_at"]),
        ]

    def __str__(self):
        user = self.user.email if self.user else "anonymous"
        return f"{user} downloaded '{self.resource.title}'"
