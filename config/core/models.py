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


class FlightSearch(models.Model):
    """Stores a user's flight search query and parsed parameters."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="flight_searches",
        null=True,
        blank=True,
    )
    natural_query = models.TextField()
    origin_airport = models.CharField(max_length=10)
    destination_airport = models.CharField(max_length=10)
    departure_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    passengers = models.PositiveSmallIntegerField(default=1)
    cabin_class = models.CharField(max_length=16, default="economy")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        route = f"{self.origin_airport} → {self.destination_airport}"
        return f"{route} ({self.departure_date})"


class FlightResult(models.Model):
    """Stores individual flight options returned from a search."""

    search = models.ForeignKey(
        FlightSearch,
        on_delete=models.CASCADE,
        related_name="results",
    )
    airline = models.CharField(max_length=100)
    flight_number = models.CharField(max_length=32, blank=True)
    departure_time = models.CharField(max_length=32)
    arrival_time = models.CharField(max_length=32)
    duration = models.CharField(max_length=32)
    stops = models.PositiveSmallIntegerField(default=0)
    price_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="USD")
    booking_url = models.URLField(blank=True)
    raw_data = models.JSONField(default=dict)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["price_cents"]

    def __str__(self) -> str:
        return f"{self.airline} ${self.price_cents / 100:.0f}"

    @property
    def price_display(self) -> str:
        return f"${self.price_cents / 100:,.0f}"


class CarRentalSearch(models.Model):
    """Stores a user's car rental search query and parsed parameters."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="car_rental_searches",
        null=True,
        blank=True,
    )
    natural_query = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    car_type = models.CharField(max_length=50, blank=True)
    max_price_per_day = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    pickup_date = models.DateField(null=True, blank=True)
    dropoff_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Car rental: {self.location} ({self.created_at:%Y-%m-%d})"


class CarRentalResult(models.Model):
    """Stores an individual car rental listing from a search."""

    search = models.ForeignKey(
        CarRentalSearch,
        on_delete=models.CASCADE,
        related_name="results",
    )
    car_name = models.CharField(max_length=200)
    car_type = models.CharField(max_length=50)
    price_per_day = models.DecimalField(max_digits=8, decimal_places=2)
    price_display = models.CharField(max_length=32)
    rental_company = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    availability = models.CharField(max_length=100, blank=True)
    listing_url = models.URLField(max_length=500, blank=True)
    source = models.CharField(max_length=100, blank=True)
    raw_data = models.JSONField(default=dict)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["price_per_day"]

    def __str__(self) -> str:
        return f"{self.car_name} - {self.price_display}"
