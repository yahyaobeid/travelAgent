from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


@dataclass
class ItineraryRequest:
    destination: str
    start_date: str
    end_date: str
    interests: str


class ItineraryGenerationError(Exception):
    """Raised when we cannot generate an itinerary via OpenAI."""


def _build_prompt(payload: ItineraryRequest) -> str:
    interests = payload.interests.strip() or "general sightseeing, dining, and culture"
    return (
        "You are a travel planning assistant. Craft a detailed daily itinerary with "
        "suggestions for morning, afternoon, and evening activities, dining "
        "recommendations, and brief rationale.\n\n"
        f"Destination: {payload.destination}\n"
        f"Dates: {payload.start_date} to {payload.end_date}\n"
        f"Traveler interests: {interests}\n\n"
        "Ensure suggestions are practical and ordered chronologically. "
        "Close with a short summary of the trip highlights."
    )


def generate_itinerary(payload: ItineraryRequest) -> tuple[str, str]:
    """
    Call OpenAI to create an itinerary.

    Returns a tuple of (prompt, itinerary_text).
    """
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        raise ImproperlyConfigured("OPENAI_API_KEY is not configured.")

    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    prompt = _build_prompt(payload)

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ItineraryGenerationError(
            "OpenAI SDK is not installed. Add 'openai' to your dependencies."
        ) from exc

    client = OpenAI(api_key=api_key)

    try:
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": "You are an expert travel planner."},
                {"role": "user", "content": prompt},
            ],
        )
    except Exception as exc:  # broad catch to wrap OpenAI errors
        raise ItineraryGenerationError(str(exc)) from exc

    itinerary_text = getattr(response, "output_text", None)
    if not itinerary_text:
        # Fallback for older SDKs
        parts: list[str] = []
        for item in getattr(response, "output", []):
            if getattr(item, "content", None):
                for block in item.content:
                    if block.type == "output_text":
                        parts.append(block.text)
        itinerary_text = "\n".join(parts)

    if not itinerary_text:
        raise ItineraryGenerationError("Received an empty response from OpenAI.")

    return prompt, itinerary_text.strip()
