from __future__ import annotations

import json
import logging
import re
from datetime import date, timedelta
from typing import Any, NamedTuple

import requests
from django.conf import settings

LOGGER = logging.getLogger(__name__)

COUNTRY_ALIASES = {
    "UNITED STATES": "US",
    "USA": "US",
    "US": "US",
    "UNITED KINGDOM": "GB",
    "UK": "GB",
    "ENGLAND": "GB",
    "SCOTLAND": "GB",
    "WALES": "GB",
    "NORTHERN IRELAND": "GB",
    "CANADA": "CA",
    "FRANCE": "FR",
    "GERMANY": "DE",
    "SPAIN": "ES",
    "ITALY": "IT",
    "PORTUGAL": "PT",
    "MEXICO": "MX",
    "AUSTRALIA": "AU",
    "NEW ZEALAND": "NZ",
    "JAPAN": "JP",
    "SINGAPORE": "SG",
    "BRAZIL": "BR",
    "IRELAND": "IE",
    "SWITZERLAND": "CH",
    "NETHERLANDS": "NL",
    "BELGIUM": "BE",
    "SWEDEN": "SE",
    "NORWAY": "NO",
}


def fetch_events(destination: str, start_date: str, end_date: str, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Fetch events for every city listed in the destination field.

    Returns approximately ``max_results`` events per city (ordered in the same sequence as provided by the user).
    """
    api_key = getattr(settings, "TICKETMASTER_API_KEY", None)
    if not api_key:
        return []

    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    destinations = _normalize_destinations(destination, start, end)
    if not destinations:
        return []

    events: list[dict[str, Any]] = []
    LOGGER.info(
        "Fetching Ticketmaster events for %d destinations between %s and %s",
        len(destinations),
        start,
        end,
    )
    for dest in destinations:
        events.extend(
            _fetch_city_events(
                destination=dest,
                start=dest.start_date,
                end=dest.end_date,
                api_key=api_key,
                max_results=max_results,
            )
        )
    return events


class Destination(NamedTuple):
    city: str
    state: str | None
    country: str
    start_date: date
    end_date: date


_DURATION_PATTERN = re.compile(r"\bfor\s+(\d+)\s*(?:day|days|night|nights)\b", re.IGNORECASE)


def _strip_duration(line: str) -> str:
    cleaned = line
    for separator in (" - ", " – ", " — "):
        if separator in cleaned:
            cleaned = cleaned.split(separator)[0]
    cleaned = _DURATION_PATTERN.sub("", cleaned)
    return cleaned.strip()


def _extract_duration_days(line: str) -> int | None:
    match = _DURATION_PATTERN.search(line)
    if not match:
        return None
    try:
        return max(1, int(match.group(1)))
    except ValueError:
        return None


def _normalize_destinations(destination_text: str, trip_start: date, trip_end: date) -> list[Destination]:
    heuristic = _heuristic_destinations(destination_text, trip_start, trip_end)
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        LOGGER.info("OPENAI_API_KEY not configured; using heuristic destination parsing.")
        return heuristic

    try:
        from openai import OpenAI
    except ImportError:
        LOGGER.warning("OpenAI SDK not installed; using heuristic destination parsing.")
        return heuristic

    model = getattr(settings, "OPENAI_DESTINATION_MODEL", getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"))
    client = OpenAI(api_key=api_key)

    system_prompt = (
        "You are an assistant that normalizes trip itineraries. "
        "Always respond with a JSON array. Each item should describe one city stay with the keys: "
        "`city` (string), `state_code` (two-letter string or null), `country_code` (ISO 3166-1 alpha-2), "
        "`start_date` (YYYY-MM-DD), and `end_date` (YYYY-MM-DD). "
        "Ensure the date ranges are continuous, do not overlap, and stay within the provided trip dates."
    )
    user_prompt = (
        "Traveler provided the following destination text:\n"
        f"{destination_text.strip() or '[no text]'}\n\n"
        f"Trip start date: {trip_start.isoformat()}\n"
        f"Trip end date: {trip_end.isoformat()}\n\n"
        "Interpret mentions such as 'for 3 days' or 'nights'. If durations are missing, divide the trip sensibly. "
        "Return ONLY the JSON array. Example output:\n"
        '[{"city":"Chicago","state_code":"IL","country_code":"US","start_date":"2025-05-01","end_date":"2025-05-03"}]'
    )

    LOGGER.info("Normalizing destinations with OpenAI model %s", model)
    LOGGER.info("Destination text provided by user: %s", destination_text)

    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
    except Exception as exc:
        LOGGER.warning("OpenAI normalization request failed: %s. Using heuristic parsing.", exc)
        return heuristic

    raw_text = _extract_output_text(response)
    LOGGER.info("OpenAI normalization raw response: %s", raw_text)

    try:
        segments = _extract_json_array(raw_text)
    except ValueError as exc:
        LOGGER.warning("Unable to parse OpenAI normalization output: %s. Using heuristic parsing.", exc)
        return heuristic

    destinations = _segments_to_destinations(segments, trip_start, trip_end)
    if not destinations:
        LOGGER.warning("OpenAI normalization returned no valid destinations; using heuristic parsing.")
        return heuristic

    LOGGER.info("OpenAI normalized destinations: %s", destinations)
    return destinations


def _heuristic_destinations(destination_text: str, trip_start: date, trip_end: date) -> list[Destination]:
    lines = [line.strip() for line in destination_text.splitlines() if line.strip()]
    if not lines:
        return [
            Destination(
                city="Unknown",
                state=None,
                country="US",
                start_date=trip_start,
                end_date=trip_end,
            )
        ]

    segments: list[tuple[str, str | None, str, int | None]] = []
    for line in lines:
        location_part = _strip_duration(line)
        parts = [segment.strip() for segment in location_part.split(",") if segment.strip()]
        if not parts:
            continue
        city = parts[0]
        state: str | None = None
        country = "US"
        if len(parts) == 2:
            country = _normalise_country(parts[1], default="US")
            if country != "US":
                state = None
        elif len(parts) >= 3:
            second = parts[1]
            last = parts[-1]
            if len(second) == 2 and second.isalpha():
                state = second.upper()
            country = _normalise_country(last, default="US")
            if country != "US":
                state = None
        duration_days = _extract_duration_days(line)
        segments.append((city, state, country, duration_days))

    if not segments:
        return [
            Destination(
                city=destination_text.strip() or "Unknown",
                state=None,
                country="US",
                start_date=trip_start,
                end_date=trip_end,
            )
        ]

    total_days = max(1, (trip_end - trip_start).days + 1)
    remaining_days = total_days
    remaining_segments = len(segments)
    current = trip_start
    destinations: list[Destination] = []

    for city, state, country, duration in segments:
        if remaining_segments <= 0 or current > trip_end:
            break

        if duration and duration > 0:
            length = min(duration, remaining_days - (remaining_segments - 1)) if remaining_segments > 1 else min(duration, remaining_days)
        else:
            if remaining_segments == 1:
                length = remaining_days
            else:
                length = max(1, remaining_days // remaining_segments)

        length = max(1, min(length, remaining_days))
        segment_end = min(trip_end, current + timedelta(days=length - 1))

        destinations.append(
            Destination(
                city=city,
                state=state if country == "US" and state else None,
                country=country,
                start_date=current,
                end_date=segment_end,
            )
        )

        current = min(trip_end, segment_end + timedelta(days=1))
        remaining_days = max(0, (trip_end - current).days + 1)
        remaining_segments -= 1

    if not destinations:
        destinations.append(
            Destination(
                city=segments[0][0] or "Unknown",
                state=segments[0][1],
                country=segments[0][2],
                start_date=trip_start,
                end_date=trip_end,
            )
        )

    LOGGER.info("Heuristic destinations: %s", destinations)
    return destinations


def _extract_output_text(response: Any) -> str:
    text = getattr(response, "output_text", "") or ""
    if text:
        return text

    parts: list[str] = []
    for item in getattr(response, "output", []):
        for block in getattr(item, "content", []):
            if getattr(block, "type", "") == "output_text":
                parts.append(getattr(block, "text", ""))
    return "\n".join(parts)


def _extract_json_array(text: str) -> list[Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\[[\s\S]*\]", text)
        if not match:
            raise ValueError("No JSON array found in OpenAI response.")
        return json.loads(match.group(0))


def _segments_to_destinations(elements: list[Any], trip_start: date, trip_end: date) -> list[Destination]:
    destinations: list[Destination] = []
    current = trip_start
    remaining_segments = len(elements)
    remaining_days = max(1, (trip_end - trip_start).days + 1)

    for raw in elements:
        if remaining_segments <= 0 or current > trip_end:
            break
        if not isinstance(raw, dict):
            continue

        city = (raw.get("city") or "").strip()
        if not city:
            continue
        state = (raw.get("state_code") or raw.get("state") or "").strip().upper() or None
        country = _normalise_country(raw.get("country_code") or raw.get("country") or "US", default="US")
        start_str = (raw.get("start_date") or "").strip()
        end_str = (raw.get("end_date") or "").strip()
        duration = raw.get("stay_length_days") or raw.get("duration_days")

        seg_start: date
        seg_end: date

        try:
            if start_str and end_str:
                seg_start = max(trip_start, date.fromisoformat(start_str))
                seg_end = min(trip_end, date.fromisoformat(end_str))
            else:
                if duration:
                    try:
                        length = max(1, int(duration))
                    except (ValueError, TypeError):
                        length = None
                else:
                    length = None

                if length:
                    seg_start = current
                    seg_end = min(trip_end, seg_start + timedelta(days=length - 1))
                else:
                    if remaining_segments == 1:
                        seg_start = current
                        seg_end = trip_end
                    else:
                        estimated = max(1, remaining_days // remaining_segments)
                        seg_start = current
                        seg_end = min(trip_end, seg_start + timedelta(days=estimated - 1))
        except ValueError:
            continue

        if seg_end < seg_start:
            seg_end = seg_start

        destinations.append(
            Destination(
                city=city,
                state=state if country == "US" else None,
                country=country,
                start_date=seg_start,
                end_date=seg_end,
            )
        )

        current = min(trip_end, seg_end + timedelta(days=1))
        remaining_days = max(0, (trip_end - current).days + 1)
        remaining_segments -= 1

    return destinations


def _normalise_country(value: str, default: str = "US") -> str:
    code = value.strip()
    if not code:
        return default
    if len(code) == 2 and code.isalpha():
        return code.upper()
    upper = code.upper()
    return COUNTRY_ALIASES.get(upper, default)


def _fetch_city_events(
    destination: Destination,
    start: date,
    end: date,
    api_key: str,
    max_results: int,
) -> list[dict[str, Any]]:
    params = {
        "apikey": api_key,
        "countryCode": destination.country,
        "city": destination.city,
        "size": max(max_results * 3, 15),
        "sort": "date,asc",
        "startDateTime": f"{start.isoformat()}T00:00:00Z",
        "endDateTime": f"{end.isoformat()}T23:59:59Z",
    }
    if destination.country == "US" and destination.state:
        params["stateCode"] = destination.state

    LOGGER.info(
        "Ticketmaster request params for %s: %s",
        destination,
        json.dumps(params, ensure_ascii=False),
    )

    try:
        response = requests.get("https://app.ticketmaster.com/discovery/v2/events.json", params=params, timeout=8)
        response.raise_for_status()
    except requests.RequestException as exc:
        LOGGER.warning("Ticketmaster API failed for %s: %s", destination.city, exc)
        return []

    data = response.json()
    LOGGER.info(
        "Ticketmaster raw response for %s (status %s): %s",
        destination,
        response.status_code,
        json.dumps(data, ensure_ascii=False),
    )
    tm_events = (data.get("_embedded") or {}).get("events", [])

    events: list[dict[str, Any]] = []
    count = 0
    for event in tm_events:
        if count >= max_results:
            break

        start_dt = (event.get("dates") or {}).get("start") or {}
        start_str = start_dt.get("dateTime") or start_dt.get("localDate")
        if not start_str:
            continue

        event_date_str = start_str[:10]
        try:
            event_date = date.fromisoformat(event_date_str)
        except ValueError:
            continue

        if not (start <= event_date <= end):
            continue

        venue_info = ((event.get("_embedded") or {}).get("venues") or [{}])[0]
        venue_city = ((venue_info.get("city") or {}).get("name") or "").strip()
        venue_state = ((venue_info.get("state") or {}).get("stateCode") or "").strip()
        venue_country = ((venue_info.get("country") or {}).get("countryCode") or "").strip()

        events.append(
            {
                "name": event.get("name"),
                "url": event.get("url"),
                "start": start_str,
                "description": (event.get("info") or event.get("pleaseNote") or "")[:160],
                "city": venue_city or destination.city,
                "state": venue_state or (destination.state or ""),
                "country": venue_country or destination.country,
                "requested_city": destination.city,
            }
        )
        count += 1

    LOGGER.info("Collected %d events for %s spanning %s to %s", count, destination.city, start, end)
    return events
