from django.conf import settings
from django.db import models


class Trip(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trips"
    )
    title = models.CharField(max_length=255, blank=True)
    itinerary = models.OneToOneField(
        "itinerary.Itinerary",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="trip"
    )
    flight_search = models.ForeignKey(
        "flights.FlightSearch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="trips"
    )
    # Note: hotel_search field is commented out because hotels app doesn't exist yet
    # hotel_search = models.ForeignKey(
    #     "hotels.HotelSearch",
    #     null=True,
    #     blank=True,
    #     on_delete=models.SET_NULL,
    #     related_name="trips"
    # )
    car_rental_search = models.ForeignKey(
        "cars.CarRentalSearch",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="trips"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or f"Trip #{self.pk}"