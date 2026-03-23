from __future__ import annotations

import logging

from .ranking import FlightQuery, FlightResult, ScoredFlight, rank_flights

LOGGER = logging.getLogger(__name__)


def search_flights(query: FlightQuery) -> list[ScoredFlight]:
    """Search for flights matching *query* and return ranked results.

    In production this would dispatch to a licensed data provider (Amadeus,
    Kiwi, etc.).  For now it returns an empty list — swap the provider
    implementation without touching ranking or view logic.
    """
    raw_flights = _fetch_from_provider(query)
    if not raw_flights:
        LOGGER.info("No flights returned by provider for query: %s", query)
        return []

    ranked = rank_flights(raw_flights)
    LOGGER.info("Ranked %d flights for query: %s", len(ranked), query)
    return ranked


def _fetch_from_provider(query: FlightQuery) -> list[FlightResult]:
    """Hook point for real flight data provider integration.

    Replace this function body with calls to Amadeus, Kiwi, SerpAPI, etc.
    Must return a list of FlightResult named tuples.
    """
    return []


def scored_to_dict(sf: ScoredFlight) -> dict:
    """Serialise a ScoredFlight to a JSON-safe dict for session storage."""
    return {
        "id": sf.flight.id,
        "source": sf.flight.source,
        "airline": sf.flight.airline,
        "flight_number": sf.flight.flight_number,
        "origin": sf.flight.origin,
        "destination": sf.flight.destination,
        "departure_datetime": sf.flight.departure_datetime,
        "arrival_datetime": sf.flight.arrival_datetime,
        "duration_minutes": sf.flight.duration_minutes,
        "stops": sf.flight.stops,
        "price_total": sf.flight.price_total,
        "baggage_carry_on": sf.flight.baggage_carry_on,
        "baggage_checked": sf.flight.baggage_checked,
        "booking_url": sf.flight.booking_url,
        "value_score": sf.value_score,
        "labels": list(sf.labels),
        "tradeoff_note": sf.tradeoff_note,
    }


def build_spotlight(scored: list[ScoredFlight]) -> dict[str, str]:
    """Return a mapping of label → flight id for the three spotlight cards."""
    spotlight: dict[str, str] = {}
    if not scored:
        return spotlight

    for sf in scored:
        if "Recommended" in sf.labels and "recommended" not in spotlight:
            spotlight["recommended"] = sf.flight.id
        if "Cheapest" in sf.labels and "cheapest" not in spotlight:
            spotlight["cheapest"] = sf.flight.id
        if "Fastest" in sf.labels and "fastest" not in spotlight:
            spotlight["fastest"] = sf.flight.id

    return spotlight
