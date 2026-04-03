import logging

from django.core.exceptions import ImproperlyConfigured
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import CarRentalResult, CarRentalSearch
from .serializers import CarRentalListingSerializer, CarRentalQuerySerializer
from .services import CarRentalSearchError, search_car_rentals_natural

LOGGER = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([AllowAny])
def car_search(request):
    serializer = CarRentalQuerySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    query = serializer.validated_data["query"]
    LOGGER.info("Car rental API search by %s: %s", request.user if request.user.is_authenticated else "anonymous", query)

    try:
        params, listings = search_car_rentals_natural(query)
    except (ImproperlyConfigured, CarRentalSearchError) as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    listing_dicts = [
        {
            "car_name": l.car_name,
            "car_type": l.car_type,
            "price_per_day": l.price_per_day,
            "price_display": l.price_display,
            "rental_company": l.rental_company,
            "location": l.location,
            "availability": l.availability,
            "listing_url": l.listing_url,
            "source": l.source,
        }
        for l in listings
    ]

    search_id = None
    if request.user.is_authenticated:
        search_obj = CarRentalSearch.objects.create(
            user=request.user,
            natural_query=query,
            location=params.location,
            car_type=params.car_type,
            max_price_per_day=params.max_price_per_day,
            pickup_date=params.pickup_date or None,
            dropoff_date=params.dropoff_date or None,
        )
        for listing in listings:
            CarRentalResult.objects.create(
                search=search_obj,
                car_name=listing.car_name,
                car_type=listing.car_type,
                price_per_day=listing.price_per_day,
                price_display=listing.price_display,
                rental_company=listing.rental_company,
                location=listing.location,
                availability=listing.availability,
                listing_url=listing.listing_url,
                source=listing.source,
                raw_data=listing.raw_data,
            )
        search_id = search_obj.pk

    return Response({
        "search_id": search_id,
        "search_params": {
            "location": params.location,
            "car_type": params.car_type,
            "max_price_per_day": params.max_price_per_day,
            "pickup_date": str(params.pickup_date) if params.pickup_date else None,
            "dropoff_date": str(params.dropoff_date) if params.dropoff_date else None,
        },
        "results": CarRentalListingSerializer(listing_dicts, many=True).data,
        "count": len(listing_dicts),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def car_detail(request, pk: int):
    try:
        search_obj = CarRentalSearch.objects.get(pk=pk, user=request.user)
    except CarRentalSearch.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    results = list(search_obj.results.values(
        "id", "car_name", "car_type", "price_per_day", "price_display",
        "rental_company", "location", "availability", "listing_url", "source",
    ))
    return Response({
        "search": {
            "id": search_obj.pk,
            "natural_query": search_obj.natural_query,
            "location": search_obj.location,
            "car_type": search_obj.car_type,
            "max_price_per_day": str(search_obj.max_price_per_day) if search_obj.max_price_per_day else None,
            "pickup_date": str(search_obj.pickup_date) if search_obj.pickup_date else None,
            "dropoff_date": str(search_obj.dropoff_date) if search_obj.dropoff_date else None,
        },
        "results": results,
    })
