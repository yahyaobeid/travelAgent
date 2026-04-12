from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.db.models import QuerySet
from typing import TYPE_CHECKING

from .models import Trip
from .serializers import TripSerializer

if TYPE_CHECKING:
    from django.contrib.auth.models import User


class TripViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Trip model providing CRUD operations.
    Only authenticated users can access and manage their own trips.
    """
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Trip]:
        """Filter trips to only return trips belonging to the current user."""
        return Trip.objects.filter(user=self.request.user).select_related(
            "itinerary",
            "flight_search",
            "car_rental_search",
        )

    def perform_create(self, serializer) -> None:
        """Set the user to the current authenticated user when creating a trip."""
        serializer.save(user=self.request.user)