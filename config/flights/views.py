import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404, redirect, render

from .intent import parse_flight_query as parse_ranked_query
from .models import FlightResult, FlightSearch
from .nl_search import FlightSearchError, search_flights_natural
from .ranking import ScoredFlight
from .services import build_spotlight, scored_to_dict, search_flights as search_ranked_flights

LOGGER = logging.getLogger(__name__)
FLIGHT_SESSION_KEY = "flight_search_results"


def search(request):
    """Render the flight search form and handle natural-language query submission."""
    if request.method == "POST":
        query_text = request.POST.get("query", "").strip()

        if not query_text:
            return render(
                request,
                "flights/search.html",
                {"error": "Please enter a search query to find flights."},
            )

        try:
            params, flights = search_flights_natural(query_text)
        except (ImproperlyConfigured, FlightSearchError) as exc:
            return render(
                request,
                "flights/search.html",
                {"query": query_text, "error": str(exc)},
            )

        LOGGER.info(
            "Flight search by %s: %s",
            request.user if request.user.is_authenticated else "anonymous",
            query_text,
        )

        if request.user.is_authenticated:
            search_obj = FlightSearch.objects.create(
                user=request.user,
                natural_query=query_text,
                origin_airport=params.origin_airport,
                destination_airport=params.destination_airport,
                departure_date=params.departure_date,
                return_date=params.return_date,
                passengers=params.passengers,
                cabin_class=params.cabin_class,
            )
            for f in flights:
                FlightResult.objects.create(
                    search=search_obj,
                    airline=f.airline,
                    flight_number=f.flight_number,
                    departure_time=f.departure_time,
                    arrival_time=f.arrival_time,
                    duration=f.duration,
                    stops=f.stops,
                    price_cents=f.price,
                    currency=f.currency,
                    booking_url=f.booking_url,
                    raw_data=f.raw_data,
                )
            return redirect("flights:detail", pk=search_obj.pk)

        # Anonymous: store in session and show results inline
        request.session[FLIGHT_SESSION_KEY] = {
            "query_text": query_text,
            "params": {
                "origin_airport": params.origin_airport,
                "destination_airport": params.destination_airport,
                "departure_date": params.departure_date,
                "return_date": params.return_date,
                "passengers": params.passengers,
                "cabin_class": params.cabin_class,
            },
            "flights": [
                {
                    "airline": f.airline,
                    "flight_number": f.flight_number,
                    "departure_time": f.departure_time,
                    "arrival_time": f.arrival_time,
                    "duration": f.duration,
                    "stops": f.stops,
                    "price": f.price,
                    "booking_url": f.booking_url,
                }
                for f in flights
            ],
        }
        return redirect("flights:results")

    return render(request, "flights/search.html", {})


def results(request):
    """Display session-stored flight results (anonymous users)."""
    payload = request.session.get(FLIGHT_SESSION_KEY)
    if not payload:
        messages.error(request, "Search for flights to see results.")
        return redirect("flights:search")

    params = payload.get("params", {})
    flights = payload.get("flights", [])

    context = {
        "query_text": payload.get("query_text", ""),
        "params": params,
        "flights": flights,
        "search": None,
    }
    return render(request, "flights/nl_results.html", context)


@login_required
def detail(request, pk: int):
    """Display saved flight search results for authenticated users."""
    search_obj = get_object_or_404(FlightSearch, pk=pk, user=request.user)
    db_results = search_obj.results.all()

    previous_searches = (
        FlightSearch.objects.filter(
            user=request.user,
            origin_airport=search_obj.origin_airport,
            destination_airport=search_obj.destination_airport,
            departure_date=search_obj.departure_date,
        )
        .exclude(pk=search_obj.pk)
        .order_by("-created_at")[:1]
    )
    price_change = None
    if previous_searches:
        prev = previous_searches[0]
        prev_cheapest = prev.results.first()
        curr_cheapest = db_results.first()
        if prev_cheapest and curr_cheapest:
            diff = curr_cheapest.price_cents - prev_cheapest.price_cents
            if diff != 0:
                price_change = {
                    "amount": abs(diff) / 100,
                    "direction": "down" if diff < 0 else "up",
                }

    return render(request, "flights/nl_results.html", {
        "search": search_obj,
        "results": db_results,
        "price_change": price_change,
    })


def ranked_results(request):
    """Display ranked flight results from the session (ranking-based search)."""
    payload = request.session.get(FLIGHT_SESSION_KEY)
    if not payload:
        messages.error(request, "Search for flights to see results.")
        return redirect("flights:search")

    flights = payload.get("flights", [])
    spotlight_ids = payload.get("spotlight", {})

    spotlight_cards = []
    seen = set()
    for key in ("recommended", "cheapest", "fastest"):
        fid = spotlight_ids.get(key)
        if fid and fid not in seen:
            match = next((f for f in flights if f["id"] == fid), None)
            if match:
                spotlight_cards.append({"label": key.capitalize(), "flight": match})
                seen.add(fid)

    context = {
        "query_text": payload.get("query_text", ""),
        "flights": flights,
        "spotlight_cards": spotlight_cards,
        "total": len(flights),
    }
    return render(request, "flights/results.html", context)
