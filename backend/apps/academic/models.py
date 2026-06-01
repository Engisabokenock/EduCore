"""Academic app models: Grade, Subject, Topic, Enrollment."""
from django.db import models
from django.utils.text import slugify

from core.models import BaseModel, TimeStampedModel


class Grade(BaseModel):
    """Educational grade level (e.g. Grade 1, Grade 8, Form 3)."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    code = models.CharField(max_length=20, unique=True, help_text="e.g. grade-1, form-3")
    order = models.PositiveSmallIntegerField(default=0, db_index=True)
    curriculum = models.CharField(
        max_length=20,
        default="CBC",
        choices=[("CBC", "Competency Based Curriculum"), ("8-4-4", "8-4-4"), ("IGCSE", "IGCSE")],
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "academic_grades"
        ordering = ["order"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Subject(BaseModel):
    """Academic subject within a grade."""
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name="subjects")
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, blank=True, db_index=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon name or emoji")
    color = models.CharField(max_length=7, default="#4F46E5", help_text="Hex color code")
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "academic_subjects"
        ordering = ["grade__order", "order", "name"]
        unique_together = [("grade", "slug")]

    def __str__(self):
        return f"{self.grade.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Topic(BaseModel):
    """Topic/unit within a subject."""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="topics")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True, db_index=True)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "academic_topics"
        ordering = ["subject__order", "order", "name"]
        unique_together = [("subject", "slug")]

    def __str__(self):
        return f"{self.subject.name} / {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Enrollment(TimeStampedModel):
    """Student enrollment in a grade/curriculum path."""
    from apps.accounts.models import User

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        SUSPENDED = "suspended", "Suspended"

    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="enrollments"
    )
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "academic_enrollments"
        unique_together = [("user", "grade")]

    def __str__(self):
        return f"{self.user.email} -> {self.grade.name}"
