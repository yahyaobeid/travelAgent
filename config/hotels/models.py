from django.conf import settings
from django.db import models


class HotelSearch(models.Model):
    """Stores a user's hotel search query and parsed parameters."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hotel_searches",
        null=True,
        blank=True,
    )
    natural_query = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    check_in_date = models.DateField(null=True, blank=True)
    check_out_date = models.DateField(null=True, blank=True)
    guests = models.PositiveSmallIntegerField(null=True, blank=True)
    max_price_per_night = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True
    )
    star_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    hotel_type = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Hotel: {self.location} ({self.created_at:%Y-%m-%d})"


class HotelResult(models.Model):
    """Stores an individual hotel listing from a search."""

    search = models.ForeignKey(
        HotelSearch,
        on_delete=models.CASCADE,
        related_name="results",
    )
    hotel_name = models.CharField(max_length=200)
    hotel_type = models.CharField(max_length=100, blank=True)
    star_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    price_per_night = models.DecimalField(max_digits=8, decimal_places=2)
    price_display = models.CharField(max_length=32)
    location = models.CharField(max_length=200, blank=True)
    amenities = models.TextField(blank=True)
    check_in = models.CharField(max_length=50, blank=True)
    check_out = models.CharField(max_length=50, blank=True)
    listing_url = models.URLField(max_length=500, blank=True)
    source = models.CharField(max_length=100, blank=True)
    raw_data = models.JSONField(default=dict)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["price_per_night"]

    def __str__(self) -> str:
        return f"{self.hotel_name} - {self.price_display}"
