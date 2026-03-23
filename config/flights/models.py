from django.conf import settings
from django.db import models


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
        db_table = "core_flightsearch"

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
        db_table = "core_flightresult"

    def __str__(self) -> str:
        return f"{self.airline} ${self.price_cents / 100:.0f}"

    @property
    def price_display(self) -> str:
        return f"${self.price_cents / 100:,.0f}"
