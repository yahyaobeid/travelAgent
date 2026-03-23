from __future__ import annotations

import json
import logging
import re
from typing import Any

from django.conf import settings

from .ranking import FlightQuery

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]

LOGGER = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a flight search assistant. Parse the user's natural language flight request "
    "and return a single JSON object with these exact keys:\n"
    "  origin (IATA airport code, string),\n"
    "  destination (IATA airport code, string),\n"
    "  departure_date (YYYY-MM-DD, string),\n"
    "  return_date (YYYY-MM-DD or null),\n"
    "  passengers (integer, default 1),\n"
    "  max_price (number or null),\n"
    "  max_stops (integer or null — 0 means nonstop only),\n"
    "  cabin_class (\"economy\", \"premium_economy\", \"business\", or \"first\", default \"economy\").\n"
    "Use today's year as a reference for relative dates. "
    "Return ONLY the JSON object, no explanation."
)


def parse_flight_query(text: str) -> FlightQuery | None:
    """Parse a natural language flight query into a structured FlightQuery.

    Returns None if OpenAI is not configured or the response cannot be parsed.
    """
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        LOGGER.info("OPENAI_API_KEY not configured; cannot parse flight query.")
        return None

    if OpenAI is None:
        LOGGER.warning("OpenAI SDK not installed; cannot parse flight query.")
        return None

    model = getattr(settings, "OPENAI_DESTINATION_MODEL", getattr(settings, "OPENAI_MODEL", "gpt-4o-mini"))
    client = OpenAI(api_key=api_key)

    LOGGER.info("Parsing flight query with OpenAI model %s: %r", model, text)

    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": text.strip()},
            ],
            temperature=0,
        )
    except Exception as exc:
        LOGGER.warning("OpenAI flight query parse failed: %s", exc)
        return None

    raw = _extract_text(response)
    LOGGER.info("OpenAI flight query raw response: %s", raw)

    data = _parse_json(raw)
    if data is None:
        LOGGER.warning("Could not parse JSON from OpenAI response: %r", raw)
        return None

    return _build_query(data)


def _extract_text(response: Any) -> str:
    text = getattr(response, "output_text", "") or ""
    if text:
        return text
    parts: list[str] = []
    for item in getattr(response, "output", []):
        for block in getattr(item, "content", []):
            if getattr(block, "type", "") == "output_text":
                parts.append(getattr(block, "text", ""))
    return "\n".join(parts)


def _parse_json(text: str) -> dict | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return None


def _build_query(data: dict) -> FlightQuery | None:
    try:
        return FlightQuery(
            origin=str(data.get("origin") or "").strip().upper(),
            destination=str(data.get("destination") or "").strip().upper(),
            departure_date=str(data.get("departure_date") or "").strip(),
            return_date=data.get("return_date") or None,
            passengers=int(data.get("passengers") or 1),
            max_price=float(data["max_price"]) if data.get("max_price") is not None else None,
            max_stops=int(data["max_stops"]) if data.get("max_stops") is not None else None,
            cabin_class=str(data.get("cabin_class") or "economy").strip(),
        )
    except (KeyError, TypeError, ValueError) as exc:
        LOGGER.warning("Could not build FlightQuery from parsed data: %s — %s", data, exc)
        return None
