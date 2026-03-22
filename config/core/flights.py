from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

LOGGER = logging.getLogger(__name__)


@dataclass
class FlightSearchParams:
    origin_airport: str
    destination_airport: str
    departure_date: str
    return_date: str | None = None
    passengers: int = 1
    cabin_class: str = "economy"


@dataclass
class FlightOption:
    airline: str
    flight_number: str
    departure_time: str
    arrival_time: str
    duration: str
    stops: int
    price: int  # cents
    currency: str = "USD"
    booking_url: str = ""
    raw_data: dict = field(default_factory=dict)


class FlightSearchError(Exception):
    """Raised when flight search fails."""


def _get_openai_client():
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        raise ImproperlyConfigured("OPENAI_API_KEY is not configured.")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise FlightSearchError(
            "OpenAI SDK is not installed. Add 'openai' to your dependencies."
        ) from exc
    return OpenAI(api_key=api_key)


def _extract_json_object(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError("No JSON object found in response.")
        return json.loads(match.group(0))


def _extract_json_array(text: str) -> list:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", text)
        if not match:
            raise ValueError("No JSON array found in response.")
        return json.loads(match.group(0))


def parse_flight_query(query: str) -> FlightSearchParams:
    """Use OpenAI to extract structured flight search params from natural language."""
    client = _get_openai_client()
    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    today = date.today().isoformat()

    system_prompt = (
        "You are a flight search assistant. Extract flight search parameters from the user's query.\n"
        "Return ONLY a JSON object with these keys:\n"
        "- origin_airport: IATA airport code (e.g. JFK, LAX, LHR)\n"
        "- destination_airport: IATA airport code\n"
        "- departure_date: YYYY-MM-DD\n"
        "- return_date: YYYY-MM-DD or null for one-way\n"
        "- passengers: integer (default 1)\n"
        "- cabin_class: economy, business, or first (default economy)\n\n"
        "Resolve city names to their primary airport IATA codes.\n"
        f"Today's date is {today}. Resolve relative dates (e.g. 'next Friday') accordingly.\n"
        "Return ONLY the JSON object, no other text."
    )

    LOGGER.info("Parsing flight query: %s", query)

    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            temperature=0,
        )
    except Exception as exc:
        raise FlightSearchError(f"Failed to parse flight query: {exc}") from exc

    raw_text = getattr(response, "output_text", "") or ""
    if not raw_text:
        for item in getattr(response, "output", []):
            for block in getattr(item, "content", []):
                if getattr(block, "type", "") == "output_text":
                    raw_text = getattr(block, "text", "")
                    break

    LOGGER.info("Parse response: %s", raw_text)

    try:
        data = _extract_json_object(raw_text)
    except (ValueError, json.JSONDecodeError) as exc:
        raise FlightSearchError(f"Could not parse flight parameters: {exc}") from exc

    return FlightSearchParams(
        origin_airport=data.get("origin_airport", "").upper(),
        destination_airport=data.get("destination_airport", "").upper(),
        departure_date=data.get("departure_date", ""),
        return_date=data.get("return_date"),
        passengers=int(data.get("passengers", 1)),
        cabin_class=data.get("cabin_class", "economy"),
    )


def search_flights(params: FlightSearchParams) -> list[FlightOption]:
    """Use OpenAI with web search to find real flight options."""
    client = _get_openai_client()
    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

    trip_type = "round trip" if params.return_date else "one-way"
    return_info = f", returning {params.return_date}" if params.return_date else ""

    search_prompt = (
        f"Search for {trip_type} flights from {params.origin_airport} to {params.destination_airport} "
        f"departing {params.departure_date}{return_info}. "
        f"{params.passengers} passenger(s), {params.cabin_class} class.\n\n"
        "Find the top 5 best flight options from Google Flights, Expedia, Kayak, or similar sources. "
        "For each flight, provide: airline name, flight number (if available), departure time, "
        "arrival time, total duration, number of stops, and price in USD.\n\n"
        "Return ONLY a JSON array of objects with these keys:\n"
        "- airline: string\n"
        "- flight_number: string (or empty string if unknown)\n"
        "- departure_time: string (e.g. '8:30 AM')\n"
        "- arrival_time: string (e.g. '4:45 PM')\n"
        "- duration: string (e.g. '7h 15m')\n"
        "- stops: integer (0 for nonstop)\n"
        "- price_usd: integer (dollar amount, e.g. 450)\n"
        "- booking_url: string (direct link if available, or empty string)\n\n"
        "Return ONLY the JSON array, no other text."
    )

    LOGGER.info("Searching flights: %s → %s on %s", params.origin_airport, params.destination_airport, params.departure_date)

    try:
        response = client.responses.create(
            model=model,
            tools=[{"type": "web_search_preview"}],
            input=[
                {"role": "user", "content": search_prompt},
            ],
        )
    except Exception as exc:
        raise FlightSearchError(f"Flight search failed: {exc}") from exc

    raw_text = getattr(response, "output_text", "") or ""
    if not raw_text:
        for item in getattr(response, "output", []):
            for block in getattr(item, "content", []):
                if getattr(block, "type", "") == "output_text":
                    raw_text = getattr(block, "text", "")
                    break

    LOGGER.info("Search response: %s", raw_text[:500])

    try:
        flights_data = _extract_json_array(raw_text)
    except (ValueError, json.JSONDecodeError) as exc:
        raise FlightSearchError(
            f"Could not parse flight results: {exc}. Raw response: {raw_text[:200]}"
        ) from exc

    options: list[FlightOption] = []
    for item in flights_data[:5]:
        if not isinstance(item, dict):
            continue
        price_usd = item.get("price_usd") or item.get("price", 0)
        try:
            price_cents = int(float(price_usd) * 100)
        except (ValueError, TypeError):
            price_cents = 0

        options.append(
            FlightOption(
                airline=item.get("airline", "Unknown"),
                flight_number=item.get("flight_number", ""),
                departure_time=item.get("departure_time", ""),
                arrival_time=item.get("arrival_time", ""),
                duration=item.get("duration", ""),
                stops=int(item.get("stops", 0)),
                price=price_cents,
                currency="USD",
                booking_url=item.get("booking_url", ""),
                raw_data=item,
            )
        )

    return options


def search_flights_natural(query: str) -> tuple[FlightSearchParams, list[FlightOption]]:
    """Top-level orchestrator: parse natural language, then search for flights."""
    params = parse_flight_query(query)

    if not params.origin_airport or not params.destination_airport or not params.departure_date:
        raise FlightSearchError(
            "Could not determine origin, destination, or date from your query. "
            "Please include departure city, destination, and travel dates."
        )

    flights = search_flights(params)
    return params, flights
