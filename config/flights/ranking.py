from __future__ import annotations

from typing import NamedTuple


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class FlightResult(NamedTuple):
    id: str
    source: str
    airline: str
    flight_number: str
    origin: str
    destination: str
    departure_datetime: str  # ISO8601
    arrival_datetime: str    # ISO8601
    duration_minutes: int
    stops: int
    price_total: float       # USD, tax-inclusive
    baggage_carry_on: bool | None = None
    baggage_checked: bool | None = None
    booking_url: str = ""


class ScoredFlight(NamedTuple):
    flight: FlightResult
    value_score: float
    labels: tuple
    tradeoff_note: str = ""


class FlightQuery(NamedTuple):
    origin: str
    destination: str
    departure_date: str       # YYYY-MM-DD
    return_date: str | None
    passengers: int = 1
    max_price: float | None = None
    max_stops: int | None = None
    preferred_airline: str | None = None
    cabin_class: str = "economy"


# ---------------------------------------------------------------------------
# Scoring weights
# ---------------------------------------------------------------------------

_WEIGHTS = {
    "price": 0.40,
    "duration": 0.20,
    "stops": 0.20,
    "departure_time": 0.10,
    "baggage": 0.10,
}

_STOPS_SCORE = {0: 100.0, 1: 60.0, 2: 20.0}


def _stops_score(stops: int) -> float:
    return _STOPS_SCORE.get(stops, 0.0)


def _departure_convenience_score(departure_datetime: str) -> float:
    """Score 0-100 based on how convenient the departure hour is.

    Morning (6-9am) and evening (6-9pm) departures score highest.
    Red-eye / late-night hours score lowest.
    """
    try:
        time_part = departure_datetime[11:16]  # "HH:MM"
        hour = int(time_part[:2])
    except (IndexError, ValueError):
        return 50.0  # neutral when unparseable

    if 6 <= hour <= 9:
        return 100.0
    if 18 <= hour <= 21:
        return 90.0
    if 10 <= hour <= 17:
        return 70.0
    if 22 <= hour <= 23 or hour == 5:
        return 30.0
    # Midnight – 4am (red-eye)
    return 10.0


def _baggage_score(carry_on: bool | None) -> float:
    if carry_on is True:
        return 100.0
    if carry_on is None:
        return 50.0
    return 0.0


def _normalize_lower_is_better(value: float, min_val: float, max_val: float) -> float:
    """Return 0-100 where min_val→100 (best) and max_val→0 (worst). Safe when equal."""
    if min_val == max_val:
        return 100.0
    return max(0.0, min(100.0, (max_val - value) / (max_val - min_val) * 100.0))


def score_flight(flight: FlightResult, all_flights: list[FlightResult]) -> float:
    """Return a composite value score (0-100) for *flight* relative to all_flights."""
    prices = [f.price_total for f in all_flights]
    durations = [f.duration_minutes for f in all_flights]

    # Lower price is better — cheapest gets 100
    price_score = _normalize_lower_is_better(flight.price_total, min(prices), max(prices))

    # Shorter duration is better — fastest gets 100
    duration_score = _normalize_lower_is_better(flight.duration_minutes, min(durations), max(durations))

    stops = _stops_score(flight.stops)
    dep = _departure_convenience_score(flight.departure_datetime)
    bag = _baggage_score(flight.baggage_carry_on)

    composite = (
        price_score * _WEIGHTS["price"]
        + duration_score * _WEIGHTS["duration"]
        + stops * _WEIGHTS["stops"]
        + dep * _WEIGHTS["departure_time"]
        + bag * _WEIGHTS["baggage"]
    )
    return max(0.0, min(100.0, composite))


# ---------------------------------------------------------------------------
# Labeling
# ---------------------------------------------------------------------------

def label_flights(scored: list[ScoredFlight]) -> list[ScoredFlight]:
    """Assign Cheapest / Fastest / Best Value / Recommended labels.

    Returns a new list; the input is not mutated.
    """
    if not scored:
        return []

    cheapest_id = min(scored, key=lambda s: s.flight.price_total).flight.id
    fastest_id = min(scored, key=lambda s: s.flight.duration_minutes).flight.id
    best_value_id = max(scored, key=lambda s: s.value_score).flight.id

    # Recommended = Best Value flight, provided it's not exclusively cheapest
    # (i.e. its price is within 120% of cheapest, meaning not an extreme outlier
    # priced far above cheapest while having a huge score advantage)
    min_price = min(s.flight.price_total for s in scored)
    best_value_flight = next(s for s in scored if s.flight.id == best_value_id)
    is_recommended = best_value_flight.value_score >= 50.0

    labeled: list[ScoredFlight] = []
    for sf in scored:
        fid = sf.flight.id
        new_labels: list[str] = list(sf.labels)

        if fid == cheapest_id:
            new_labels.append("Cheapest")
        if fid == fastest_id:
            new_labels.append("Fastest")
        if fid == best_value_id:
            new_labels.append("Best Value")
            if is_recommended:
                new_labels.append("Recommended")

        labeled.append(ScoredFlight(
            flight=sf.flight,
            value_score=sf.value_score,
            labels=tuple(new_labels),
            tradeoff_note=sf.tradeoff_note,
        ))

    return labeled


# ---------------------------------------------------------------------------
# Tradeoff note
# ---------------------------------------------------------------------------

def generate_tradeoff_note(cheapest: FlightResult, recommended: FlightResult) -> str:
    """Return a plain-English tradeoff sentence comparing cheapest to recommended.

    Returns empty string when both flights are the same.
    """
    if cheapest.id == recommended.id:
        return ""

    price_diff = round(recommended.price_total - cheapest.price_total)
    time_diff_min = recommended.duration_minutes - cheapest.duration_minutes

    parts: list[str] = []

    if price_diff > 0:
        parts.append(f"costs ${price_diff} more")
    elif price_diff < 0:
        parts.append(f"saves ${abs(price_diff)}")

    if time_diff_min < 0:
        hours, mins = divmod(abs(time_diff_min), 60)
        if hours and mins:
            parts.append(f"is {hours}h {mins}m faster")
        elif hours:
            parts.append(f"is {hours} hour{'s' if hours > 1 else ''} faster")
        else:
            parts.append(f"is {mins} minutes faster")
    elif time_diff_min > 0:
        hours, mins = divmod(time_diff_min, 60)
        if hours and mins:
            parts.append(f"takes {hours}h {mins}m longer")
        elif hours:
            parts.append(f"takes {hours} hour{'s' if hours > 1 else ''} longer")
        else:
            parts.append(f"takes {mins} minutes longer")

    if not parts:
        return ""

    note = f"Our recommended option {' and '.join(parts)}."
    return note


# ---------------------------------------------------------------------------
# Full ranking pipeline
# ---------------------------------------------------------------------------

def rank_flights(flights: list[FlightResult]) -> list[ScoredFlight]:
    """Score, label, and sort flights by value score descending."""
    if not flights:
        return []

    scored = [
        ScoredFlight(flight=f, value_score=score_flight(f, flights), labels=())
        for f in flights
    ]
    labeled = label_flights(scored)

    # Attach tradeoff note to cheapest flight (vs recommended)
    cheapest = min(labeled, key=lambda s: s.flight.price_total)
    recommended_candidates = [s for s in labeled if "Recommended" in s.labels]
    recommended = recommended_candidates[0] if recommended_candidates else cheapest

    result: list[ScoredFlight] = []
    for sf in labeled:
        note = ""
        if sf.flight.id == cheapest.flight.id and cheapest.flight.id != recommended.flight.id:
            note = generate_tradeoff_note(sf.flight, recommended.flight)
        result.append(ScoredFlight(
            flight=sf.flight,
            value_score=sf.value_score,
            labels=sf.labels,
            tradeoff_note=note,
        ))

    result.sort(key=lambda s: s.value_score, reverse=True)
    return result
