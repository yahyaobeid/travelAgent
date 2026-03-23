import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404, redirect, render

from rest_framework import status as drf_status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .forms import CarRentalSearchForm
from .models import CarRentalResult, CarRentalSearch
from .serializers import CarRentalListingSerializer, CarRentalQuerySerializer
from .services import CarRentalSearchError, search_car_rentals_natural

LOGGER = logging.getLogger(__name__)


def car_rental_search(request):
    """Accept a natural-language car rental query, search via AI, and display results."""
    if request.method == "POST":
        form = CarRentalSearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data["query"]
            LOGGER.info(
                "Car rental search by %s: %s",
                request.user if request.user.is_authenticated else "anonymous",
                query,
            )
            try:
                params, listings = search_car_rentals_natural(query)
            except (ImproperlyConfigured, CarRentalSearchError) as exc:
                form.add_error(None, str(exc))
            else:
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
                    return redirect("cars:detail", pk=search_obj.pk)

                # Anonymous: render results inline
                return render(request, "cars/results.html", {
                    "params": params,
                    "listings": listings,
                    "search": None,
                })
    else:
        form = CarRentalSearchForm()

    return render(request, "cars/search.html", {"form": form})


@login_required
def car_rental_results(request, pk: int):
    """Display saved car rental search results."""
    search_obj = get_object_or_404(CarRentalSearch, pk=pk, user=request.user)
    results = search_obj.results.all()

    return render(request, "cars/results.html", {
        "search": search_obj,
        "results": results,
    })


@api_view(["POST"])
def car_rental_search_api(request):
    """DRF endpoint: accepts {"query": "..."}, returns structured car rental listings."""
    serializer = CarRentalQuerySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    query = serializer.validated_data["query"]

    try:
        params, listings = search_car_rentals_natural(query)
    except (ImproperlyConfigured, CarRentalSearchError) as exc:
        return Response({"error": str(exc)}, status=drf_status.HTTP_400_BAD_REQUEST)

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

    return Response({
        "search_params": {
            "location": params.location,
            "car_type": params.car_type,
            "max_price_per_day": params.max_price_per_day,
            "pickup_date": params.pickup_date,
            "dropoff_date": params.dropoff_date,
        },
        "results": CarRentalListingSerializer(listing_dicts, many=True).data,
        "count": len(listing_dicts),
    })
