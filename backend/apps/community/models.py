"""Community app models: Review, Rating."""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from core.models import BaseModel


class Review(BaseModel):
    """User review and rating for a resource."""

    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="reviews"
    )
    resource = models.ForeignKey(
        "content.Resource", on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(default=True)

    class Meta:
        db_table = "community_reviews"
        unique_together = [("user", "resource")]
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["resource", "is_approved"])]

    def __str__(self):
        return f"{self.user.email} rated {self.resource.title} {self.rating}/5"
