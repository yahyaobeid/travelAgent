import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404, redirect, render

from .forms import HotelSearchForm
from .models import HotelResult, HotelSearch
from .services import HotelSearchError, search_hotels_natural

LOGGER = logging.getLogger(__name__)


def hotel_search(request):
    """Accept a natural-language hotel query, search via AI, and display results."""
    if request.method == "POST":
        form = HotelSearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data["query"]
            LOGGER.info(
                "Hotel search by %s: %s",
                request.user if request.user.is_authenticated else "anonymous",
                query,
            )
            try:
                params, listings = search_hotels_natural(query)
            except (ImproperlyConfigured, HotelSearchError) as exc:
                form.add_error(None, str(exc))
            else:
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
                    return redirect("hotels:detail", pk=search_obj.pk)

                return render(request, "hotels/results.html", {
                    "params": params,
                    "listings": listings,
                    "search": None,
                })
    else:
        form = HotelSearchForm()

    return render(request, "hotels/search.html", {"form": form})


@login_required
def hotel_results(request, pk: int):
    """Display saved hotel search results."""
    search_obj = get_object_or_404(HotelSearch, pk=pk, user=request.user)
    results = search_obj.results.all()

    return render(request, "hotels/results.html", {
        "search": search_obj,
        "results": results,
    })
