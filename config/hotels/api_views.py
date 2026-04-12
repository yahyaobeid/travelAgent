import logging

from django.core.exceptions import ImproperlyConfigured
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import HotelResult, HotelSearch
from .serializers import HotelListingSerializer, HotelQuerySerializer
from .services import HotelSearchError, search_hotels_natural

LOGGER = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([AllowAny])
def hotel_search(request):
    serializer = HotelQuerySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    query = serializer.validated_data["query"]
    LOGGER.info(
        "Hotel API search by %s: %s",
        request.user if request.user.is_authenticated else "anonymous",
        query,
    )

    try:
        params, listings = search_hotels_natural(query)
    except (ImproperlyConfigured, HotelSearchError) as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    listing_dicts = [
        {
            "hotel_name": l.hotel_name,
            "hotel_type": l.hotel_type,
            "star_rating": l.star_rating,
            "price_per_night": l.price_per_night,
            "price_display": l.price_display,
            "location": l.location,
            "amenities": l.amenities,
            "check_in": l.check_in,
            "check_out": l.check_out,
            "listing_url": l.listing_url,
            "source": l.source,
        }
        for l in listings
    ]

    search_id = None
    if request.user.is_authenticated:
        search_obj = HotelSearch.objects.create(
            user=request.user,
            natural_query=query,
            location=params.location,
            check_in_date=params.check_in_date or None,
            check_out_date=params.check_out_date or None,
            guests=params.guests,
            max_price_per_night=params.max_price_per_night,
            star_rating=params.star_rating,
            hotel_type=params.hotel_type,
        )
        for listing in listings:
            HotelResult.objects.create(
                search=search_obj,
                hotel_name=listing.hotel_name,
                hotel_type=listing.hotel_type,
                star_rating=listing.star_rating,
                price_per_night=listing.price_per_night,
                price_display=listing.price_display,
                location=listing.location,
                amenities=listing.amenities,
                check_in=listing.check_in,
                check_out=listing.check_out,
                listing_url=listing.listing_url,
                source=listing.source,
                raw_data=listing.raw_data,
            )
        search_id = search_obj.pk

    return Response({
        "search_id": search_id,
        "search_params": {
            "location": params.location,
            "check_in_date": params.check_in_date or None,
            "check_out_date": params.check_out_date or None,
            "guests": params.guests,
            "max_price_per_night": params.max_price_per_night,
            "star_rating": params.star_rating,
            "hotel_type": params.hotel_type,
        },
        "results": HotelListingSerializer(listing_dicts, many=True).data,
        "count": len(listing_dicts),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def hotel_detail(request, pk: int):
    try:
        search_obj = HotelSearch.objects.get(pk=pk, user=request.user)
    except HotelSearch.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    results = list(search_obj.results.values(
        "id", "hotel_name", "hotel_type", "star_rating", "price_per_night",
        "price_display", "location", "amenities", "check_in", "check_out",
        "listing_url", "source",
    ))
    return Response({
        "search": {
            "id": search_obj.pk,
            "natural_query": search_obj.natural_query,
            "location": search_obj.location,
            "check_in_date": str(search_obj.check_in_date) if search_obj.check_in_date else None,
            "check_out_date": str(search_obj.check_out_date) if search_obj.check_out_date else None,
            "guests": search_obj.guests,
            "max_price_per_night": str(search_obj.max_price_per_night) if search_obj.max_price_per_night else None,
            "star_rating": search_obj.star_rating,
            "hotel_type": search_obj.hotel_type,
        },
        "results": results,
    })
