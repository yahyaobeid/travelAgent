from django.conf import settings
from django.db import models

from .utils import render_markdown


class Itinerary(models.Model):
    """Stores generated itineraries for a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="itineraries",
    )
    destination = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    interests = models.TextField(blank=True)
    prompt = models.TextField()
    generated_plan = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.destination} ({self.start_date:%b %d} - {self.end_date:%b %d})"

    @property
    def rendered_plan(self) -> str:
        """Return the itinerary content converted from markdown to HTML."""
        return render_markdown(self.generated_plan)
