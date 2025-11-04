from django.conf import settings
from django.db import models

from .utils import render_markdown


class Itinerary(models.Model):
    """Stores generated itineraries for a user."""

    STYLE_GENERAL = "general"
    STYLE_CULTURE = "culture_history"
    STYLE_CITY = "city_shopping"
    STYLE_ADVENTURE = "adventure"

    STYLE_CHOICES = [
        (STYLE_GENERAL, "No preference / Balanced"),
        (STYLE_CULTURE, "Culture & History"),
        (STYLE_CITY, "City Life & Shopping"),
        (STYLE_ADVENTURE, "Adventure & Outdoors"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="itineraries",
    )
    destination = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    interests = models.TextField(blank=True)
    activities = models.TextField(blank=True, help_text="Specific activities or experiences the traveler wants to prioritise.")
    food_preferences = models.TextField(
        blank=True,
        help_text="Cuisine preferences, must-try drinks, and any dietary restrictions to keep in mind.",
    )
    preference = models.CharField(
        max_length=32,
        choices=STYLE_CHOICES,
        default=STYLE_GENERAL,
        help_text="Overall tone for the generated itinerary.",
    )
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
