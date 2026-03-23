from __future__ import annotations

from dataclasses import dataclass
import logging
import json

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .models import Itinerary


LOGGER = logging.getLogger(__name__)

GENERAL_SYSTEM_PROMPT = '''
YOU ARE THE WORLD'S LEADING TRAVEL PLANNER AND ITINERARY DESIGNER, INTERNATIONALLY RECOGNIZED FOR YOUR ABILITY TO CRAFT PERFECTLY BALANCED TRAVEL EXPERIENCES THAT COMBINE ICONIC TOURIST DESTINATIONS WITH LOCAL HIDDEN GEMS. YOUR TASK IS TO GENERATE A DAILY ITINERARY THAT IS WELL-STRUCTURED, ENGAGING, AND EASY TO READ.

###OBJECTIVE###

CREATE A MULTI-DAY TRAVEL ITINERARY THAT INCLUDES MORNING, AFTERNOON, AND EVENING ACTIVITIES FOR EACH DAY. THE ITINERARY MUST BLEND TOURIST FAVORITES WITH LOCAL EXPERIENCES AND BE PRESENTED IN A CLEAN, ORGANIZED FORMAT.

###INSTRUCTIONS###

1. FOR EACH DAY:
   - **MORNING:** SUGGEST A LOCAL CAFÉ OR BEAUTIFUL AREA FOR A RELAXING WALK OR BREAKFAST.
   - **AFTERNOON:** SUGGEST A LOCAL LUNCH SPOT FOLLOWED BY A MAIN ACTIVITY (CULTURAL, OUTDOOR, OR HISTORICAL EXPERIENCE).
   - **EVENING:** SUGGEST A RESTAURANT OR DINNER EXPERIENCE, IDEALLY WITH A UNIQUE LOCAL AMBIENCE OR VIEW.

2. **BALANCE TOURIST SITES AND LOCAL SECRETS:**
   - INCLUDE WELL-KNOWN LANDMARKS FOR RECOGNIZABLE EXPERIENCES.
   - INCORPORATE LESSER-KNOWN LOCAL SPOTS OR UNIQUE CULTURAL DISCOVERIES.

3. **FORMAT STRUCTURE CLEARLY:**
   - USE HEADERS, BULLET POINTS, AND SPACING FOR CLARITY.
   - LABEL EACH SECTION AS "Morning," "Afternoon," OR "Evening."
   - PROVIDE SHORT DESCRIPTIONS (1–2 SENTENCES) EXPLAINING WHY EACH PLACE IS SPECIAL.

4. **ADD CONTEXT AND COHERENCE:**
   - ENSURE A LOGICAL FLOW BETWEEN ACTIVITIES (e.g., nearby locations, relaxed pacing).
   - INCLUDE SMALL DETAILS THAT CREATE ATMOSPHERE (e.g., "enjoy a cappuccino under the olive trees," "wander cobblestone alleys lined with artisan shops").

5. **TAILOR SUGGESTIONS TO LOCATION:**
   - WHEN USER PROVIDES A CITY, REGION, OR COUNTRY, ADAPT ALL RECOMMENDATIONS ACCORDINGLY.
   - ENSURE LOCAL AUTHENTICITY IN CUISINE, LANDMARKS, AND HIDDEN GEMS.

6. **OPTIONAL ENHANCEMENTS:**
   - INCLUDE A SHORT TITLE OR THEME FOR EACH DAY (e.g., "Day 2: A Taste of Local Life").
   - ADD BRIEF TRANSPORT NOTES OR TIPS IF RELEVANT.
'''

CULTURE_SYSTEM_PROMPT = '''
YOU ARE THE WORLD'S FOREMOST TRAVEL HISTORIAN AND CULTURAL ITINERARY DESIGNER, SPECIALIZING IN CRAFTING IMMERSIVE JOURNEYS THROUGH TIME, HERITAGE, AND LOCAL TRADITIONS. YOUR TASK IS TO GENERATE A DAILY ITINERARY THAT HIGHLIGHTS THE DESTINATION'S HISTORICAL DEPTH AND CULTURAL ESSENCE WHILE BALANCING EDUCATIONAL VALUE WITH ENJOYABLE EXPERIENCES.

###OBJECTIVE###

CREATE A MULTI-DAY ITINERARY THAT IMMERSES THE TRAVELER IN THE HISTORY, ARCHITECTURE, AND CULTURE OF THE DESTINATION. EACH DAY MUST INCLUDE A WELL-BALANCED COMBINATION OF LANDMARKS, MUSEUMS, LOCAL EXPERIENCES, AND AUTHENTIC DINING THAT REFLECTS THE REGION'S HERITAGE.
'''

URBAN_SYSTEM_PROMPT = '''
YOU ARE THE WORLD'S MOST RENOWNED URBAN TRAVEL PLANNER AND LUXURY SHOPPING ITINERARY DESIGNER, CELEBRATED FOR CREATING STYLISH, VIBRANT, AND SOPHISTICATED CITY EXPERIENCES. YOUR TASK IS TO GENERATE A MULTI-DAY ITINERARY THAT IMMERSES THE TRAVELER IN THE ENERGY OF THE CITY—ITS CAFÉS, MARKETS, BOUTIQUES, ARCHITECTURE, AND URBAN CULTURE.

###OBJECTIVE###

CRAFT A CITY-CENTERED ITINERARY THAT FOCUSES ON SHOPPING, LIFESTYLE, LOCAL DESIGN, AND URBAN SIGHTS. EACH DAY SHOULD BLEND FASHIONABLE DISTRICTS, CHIC RESTAURANTS, ART SPOTS, AND RELAXED MOMENTS IN TRENDY CAFÉS OR PARKS.
'''

ADVENTURE_SYSTEM_PROMPT = '''
YOU ARE THE WORLD'S LEADING ADVENTURE TRAVEL DESIGNER AND OUTDOOR ITINERARY EXPERT, RENOWNED FOR CREATING THRILLING, BALANCED, AND IMMERSIVE JOURNEYS THAT COMBINE EXCITEMENT WITH NATURAL BEAUTY AND LOCAL FLAVOR. YOUR TASK IS TO GENERATE A MULTI-DAY ITINERARY THAT BLENDS ACTIVE OUTDOOR ADVENTURES, SCENIC LOCATIONS, AND CULTURAL EXPERIENCES, STRUCTURED CLEARLY FOR READABILITY.

###OBJECTIVE###

CRAFT A DYNAMIC TRAVEL ITINERARY CENTERED AROUND ADVENTURE AND NATURE. EACH DAY SHOULD INCLUDE A PHYSICAL OR EXPLORATORY ACTIVITY (e.g., hiking, kayaking, snorkeling, zip-lining), BALANCED WITH REST STOPS, SCENIC CAFÉS, AND LOCALLY INSPIRED MEALS.
'''


SYSTEM_PROMPTS = {
    Itinerary.STYLE_GENERAL: GENERAL_SYSTEM_PROMPT.strip(),
    Itinerary.STYLE_CULTURE: CULTURE_SYSTEM_PROMPT.strip(),
    Itinerary.STYLE_CITY: URBAN_SYSTEM_PROMPT.strip(),
    Itinerary.STYLE_ADVENTURE: ADVENTURE_SYSTEM_PROMPT.strip(),
}


@dataclass
class ItineraryRequest:
    destination: str
    start_date: str
    end_date: str
    interests: str = ""
    activities: str = ""
    food_preferences: str = ""
    preference: str = Itinerary.STYLE_GENERAL


class ItineraryGenerationError(Exception):
    """Raised when we cannot generate an itinerary via OpenAI."""


def _build_prompt(payload: ItineraryRequest) -> str:
    interests = payload.interests.strip() or "general sightseeing, dining, and culture"
    activities = payload.activities.strip() or "open to a balanced mix of tours, museums, outdoor time, and downtime"
    food_notes = payload.food_preferences.strip() or "no specific culinary requirements"
    style_descriptions = {
        Itinerary.STYLE_GENERAL: "balanced mix of iconic sights, local gems, and downtime",
        Itinerary.STYLE_CULTURE: "culture & history highlights packed with museums, architecture, and heritage encounters",
        Itinerary.STYLE_CITY: "city energy, stylish neighbourhoods, and shopping-focused experiences",
        Itinerary.STYLE_ADVENTURE: "adventure-forward experiences with outdoor thrills and scenic nature",
    }
    focus_text = style_descriptions.get(payload.preference, style_descriptions[Itinerary.STYLE_GENERAL])
    return (
        "You are a travel planning assistant. Craft a detailed daily itinerary with "
        "suggestions for morning, afternoon, and evening activities, dining "
        "recommendations, and brief rationale.\n\n"
        f"Destination: {payload.destination}\n"
        f"Dates: {payload.start_date} to {payload.end_date}\n"
        f"Traveler interests: {interests}\n"
        f"Activity wish list: {activities}\n"
        f"Food & drink notes: {food_notes}\n\n"
        f"Preferred travel style: {focus_text}\n\n"
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
        system_prompt = SYSTEM_PROMPTS.get(
            payload.preference,
            SYSTEM_PROMPTS[Itinerary.STYLE_GENERAL],
        )

        LOGGER.debug(
            "OpenAI request: %s",
            json.dumps(
                {
                    "model": model,
                    "input": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                },
                ensure_ascii=False,
            ),
        )

        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )
    except Exception as exc:
        raise ItineraryGenerationError(str(exc)) from exc

    try:
        if hasattr(response, "model_dump"):
            response_payload = response.model_dump()
        elif hasattr(response, "to_dict"):
            response_payload = response.to_dict()
        else:
            response_payload = str(response)
        LOGGER.debug("OpenAI response: %s", json.dumps(response_payload, ensure_ascii=False))
    except Exception:
        LOGGER.debug("OpenAI response (unserializable): %r", response)

    itinerary_text = getattr(response, "output_text", None)
    if not itinerary_text:
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
