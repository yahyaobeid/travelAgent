from django.conf import settings
from django.db import models


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
        db_table = "core_carrentalsearch"

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
        db_table = "core_carrentalresult"

    def __str__(self) -> str:
        return f"{self.car_name} - {self.price_display}"
