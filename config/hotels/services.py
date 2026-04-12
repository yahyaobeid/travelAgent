from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

LOGGER = logging.getLogger(__name__)

MAX_AGENT_ITERATIONS = 10
TARGET_LISTINGS = 20
SCRAPE_MAX_CHARS = 15_000
SCRAPE_TIMEOUT = 10
SEARCH_PAUSE = 1.5

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class HotelSearchParams:
    location: str
    check_in_date: str = ""
    check_out_date: str = ""
    guests: int | None = None
    max_price_per_night: float | None = None
    star_rating: int | None = None
    hotel_type: str = ""


@dataclass
class HotelListing:
    hotel_name: str
    hotel_type: str
    star_rating: int | None
    price_per_night: float
    price_display: str
    location: str
    amenities: str
    check_in: str
    check_out: str
    listing_url: str
    source: str
    raw_data: dict = field(default_factory=dict)


class HotelSearchError(Exception):
    """Raised when hotel search fails."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_openai_client():
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        raise ImproperlyConfigured("OPENAI_API_KEY is not configured.")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise HotelSearchError(
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


# ---------------------------------------------------------------------------
# Tool definitions for OpenAI function calling
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_google",
            "description": (
                "Search Google for hotel listings. Returns a list of top result "
                "URLs and snippets. Use specific queries including location, dates, "
                "star rating, and budget to find relevant hotel pages."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The Google search query string",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_page",
            "description": (
                "Fetch a web page and return its cleaned text content. Use this to "
                "read the content of hotel listing pages found via search."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch and parse",
                    }
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "extract_hotel_listings",
            "description": (
                "Extract structured hotel listing data from raw page text. "
                "Returns a JSON array of hotel objects with price, name, amenities, "
                "and links. Use this after scraping a page to get structured data."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "raw_text": {
                        "type": "string",
                        "description": "The raw text content from a scraped page",
                    },
                    "source_url": {
                        "type": "string",
                        "description": "The URL the text was scraped from",
                    },
                },
                "required": ["raw_text", "source_url"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _tool_search_google(query: str) -> list[dict]:
    try:
        from googlesearch import search as gsearch
    except ImportError as exc:
        raise HotelSearchError("googlesearch-python is not installed.") from exc

    LOGGER.info("Google search: %s", query)
    results = []
    try:
        for url in gsearch(query, num_results=10):
            results.append({"url": url, "title": "", "snippet": ""})
            time.sleep(0.2)
    except Exception as exc:
        LOGGER.warning("Google search error: %s", exc)
        return [{"error": f"Search failed: {exc}"}]

    time.sleep(SEARCH_PAUSE)
    return results


def _tool_scrape_page(url: str) -> str:
    LOGGER.info("Scraping: %s", url)
    try:
        resp = requests.get(
            url,
            timeout=SCRAPE_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        LOGGER.warning("Scrape failed for %s: %s", url, exc)
        return f"Error fetching page: {exc}"

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    return text[:SCRAPE_MAX_CHARS]


def _tool_extract_hotel_listings(
    raw_text: str, source_url: str, client, model: str
) -> list[dict]:
    domain = urlparse(source_url).netloc

    system_prompt = (
        "You are a data extraction assistant. Extract hotel listing information "
        "from the provided text. Return ONLY a JSON array of objects. Each object must have:\n"
        '- "hotel_name": string (e.g. "The Grand Hotel")\n'
        '- "hotel_type": string (e.g. "Hotel", "Resort", "Boutique", "Hostel", "Motel")\n'
        '- "star_rating": integer (1-5) or null if not available\n'
        '- "price_per_night": number (USD, e.g. 150.0)\n'
        '- "price_display": string (e.g. "$150/night")\n'
        '- "location": string (address or neighborhood)\n'
        '- "amenities": string (comma-separated list, e.g. "WiFi, Pool, Gym, Breakfast")\n'
        '- "check_in": string (check-in time or date, e.g. "3:00 PM" or "2024-03-28")\n'
        '- "check_out": string (check-out time or date)\n'
        '- "listing_url": string (direct link if found in text, otherwise "")\n'
        f'- "source": "{domain}"\n\n'
        "If you cannot extract valid listings from the text, return an empty array [].\n"
        "Return ONLY the JSON array, no other text."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            max_tokens=4096,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text[:SCRAPE_MAX_CHARS]},
            ],
        )
    except Exception as exc:
        LOGGER.warning("Extract hotel listings failed: %s", exc)
        return []

    result_text = response.choices[0].message.content or ""

    try:
        listings = _extract_json_array(result_text)
    except (ValueError, json.JSONDecodeError):
        LOGGER.warning("Could not parse extracted hotel listings JSON")
        return []

    valid = []
    for item in listings:
        if not isinstance(item, dict):
            continue
        if item.get("hotel_name") and item.get("price_per_night"):
            item.setdefault("source", domain)
            item.setdefault("listing_url", source_url)
            item.setdefault("hotel_type", "")
            item.setdefault("star_rating", None)
            item.setdefault("location", "")
            item.setdefault("amenities", "")
            item.setdefault("check_in", "")
            item.setdefault("check_out", "")
            item.setdefault("price_display", f"${item['price_per_night']}/night")
            valid.append(item)

    return valid


# ---------------------------------------------------------------------------
# Dispatch tool calls
# ---------------------------------------------------------------------------

def _dispatch_tool(name: str, input_data: dict, client, model: str):
    if name == "search_google":
        results = _tool_search_google(input_data["query"])
        return json.dumps(results)
    elif name == "scrape_page":
        return _tool_scrape_page(input_data["url"])
    elif name == "extract_hotel_listings":
        listings = _tool_extract_hotel_listings(
            input_data["raw_text"],
            input_data["source_url"],
            client,
            model,
        )
        return json.dumps(listings)
    else:
        return json.dumps({"error": f"Unknown tool: {name}"})


# ---------------------------------------------------------------------------
# Parse natural language query
# ---------------------------------------------------------------------------

def parse_hotel_query(query: str) -> HotelSearchParams:
    """Use OpenAI to extract structured hotel search params from natural language."""
    client = _get_openai_client()
    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
    today = date.today().isoformat()

    system_prompt = (
        "You are a hotel search assistant. Extract search parameters from the user's query.\n"
        "Return ONLY a JSON object with these keys:\n"
        '- "location": string (city or area, e.g. "Paris, France")\n'
        '- "check_in_date": string (YYYY-MM-DD) or ""\n'
        '- "check_out_date": string (YYYY-MM-DD) or ""\n'
        '- "guests": integer or null (number of guests)\n'
        '- "max_price_per_night": number or null (USD budget per night)\n'
        '- "star_rating": integer (1-5) or null (minimum star rating desired)\n'
        '- "hotel_type": string (e.g. "Hotel", "Resort", "Hostel", or "" if not specified)\n\n'
        f"Today's date is {today}. Resolve relative dates (e.g. 'next weekend') accordingly.\n"
        "Return ONLY the JSON object, no other text."
    )

    LOGGER.info("Parsing hotel query: %s", query)

    try:
        response = client.chat.completions.create(
            model=model,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
        )
    except Exception as exc:
        raise HotelSearchError(f"Failed to parse hotel query: {exc}") from exc

    raw_text = response.choices[0].message.content or ""
    LOGGER.info("Parse response: %s", raw_text)

    try:
        data = _extract_json_object(raw_text)
    except (ValueError, json.JSONDecodeError) as exc:
        raise HotelSearchError(
            f"Could not parse hotel search parameters: {exc}"
        ) from exc

    max_price = data.get("max_price_per_night")
    if max_price is not None:
        try:
            max_price = float(max_price)
        except (ValueError, TypeError):
            max_price = None

    guests = data.get("guests")
    if guests is not None:
        try:
            guests = int(guests)
        except (ValueError, TypeError):
            guests = None

    star_rating = data.get("star_rating")
    if star_rating is not None:
        try:
            star_rating = int(star_rating)
        except (ValueError, TypeError):
            star_rating = None

    return HotelSearchParams(
        location=data.get("location", ""),
        check_in_date=data.get("check_in_date", ""),
        check_out_date=data.get("check_out_date", ""),
        guests=guests,
        max_price_per_night=max_price,
        star_rating=star_rating,
        hotel_type=data.get("hotel_type", ""),
    )


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

def search_hotels(params: HotelSearchParams) -> list[HotelListing]:
    """Run the OpenAI agent loop to find hotel listings."""
    client = _get_openai_client()
    model = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")

    system_prompt = (
        "You are a hotel search agent. Your goal is to find exactly 20 hotel "
        "listings matching the user's criteria.\n\n"
        "Strategy:\n"
        "1. Use search_google to find hotel listings (try sites like Booking.com, "
        "Hotels.com, Expedia, Kayak, Trivago, Agoda, TripAdvisor, etc.)\n"
        "2. Use scrape_page to fetch promising result pages\n"
        "3. Use extract_hotel_listings to pull structured data from the scraped content\n"
        "4. Keep searching and scraping until you have accumulated 20 listings\n"
        "5. If a page fails to scrape or yields no results, try the next one\n"
        "6. Vary your search queries to cover different hotel types, areas, and price ranges\n\n"
        "Important: Call tools one step at a time. Search first, then scrape results, "
        "then extract listings. Repeat until you have enough listings."
    )

    parts = [f"Find hotels in {params.location}."]
    if params.check_in_date:
        parts.append(f"Check-in: {params.check_in_date}.")
    if params.check_out_date:
        parts.append(f"Check-out: {params.check_out_date}.")
    if params.guests:
        parts.append(f"Guests: {params.guests}.")
    if params.max_price_per_night:
        parts.append(f"Budget: under ${params.max_price_per_night}/night.")
    if params.star_rating:
        parts.append(f"Minimum star rating: {params.star_rating} stars.")
    if params.hotel_type:
        parts.append(f"Hotel type: {params.hotel_type}.")
    parts.append(f"Find {TARGET_LISTINGS} hotel listings with prices and details.")

    user_message = " ".join(parts)
    LOGGER.info("Agent user message: %s", user_message)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    all_listings: list[dict] = []

    for iteration in range(MAX_AGENT_ITERATIONS):
        LOGGER.info("Agent iteration %d, listings so far: %d", iteration + 1, len(all_listings))

        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=4096,
                messages=messages,
                tools=TOOLS,
            )
        except Exception as exc:
            LOGGER.error("Agent API call failed: %s", exc)
            break

        message = response.choices[0].message
        messages.append(message)

        if not message.tool_calls:
            LOGGER.info("Agent stopped (no tool calls)")
            break

        for tc in message.tool_calls:
            input_data = json.loads(tc.function.arguments)
            LOGGER.info("Tool call: %s(%s)", tc.function.name, json.dumps(input_data)[:200])
            result_str = _dispatch_tool(tc.function.name, input_data, client, model)

            if tc.function.name == "extract_hotel_listings":
                try:
                    extracted = json.loads(result_str)
                    if isinstance(extracted, list):
                        all_listings.extend(extracted)
                        LOGGER.info(
                            "Extracted %d listings (total: %d)", len(extracted), len(all_listings)
                        )
                except (json.JSONDecodeError, TypeError):
                    pass

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_str[:SCRAPE_MAX_CHARS],
            })

        if len(all_listings) >= TARGET_LISTINGS:
            LOGGER.info("Reached target of %d listings", TARGET_LISTINGS)
            break

    # Deduplicate by (hotel_name, location, price_per_night)
    seen = set()
    unique: list[HotelListing] = []
    for item in all_listings:
        key = (
            item.get("hotel_name", ""),
            item.get("location", ""),
            item.get("price_per_night", 0),
        )
        if key in seen:
            continue
        seen.add(key)
        try:
            star = item.get("star_rating")
            listing = HotelListing(
                hotel_name=item.get("hotel_name", "Unknown"),
                hotel_type=item.get("hotel_type", ""),
                star_rating=int(star) if star is not None else None,
                price_per_night=float(item.get("price_per_night", 0)),
                price_display=item.get("price_display", ""),
                location=item.get("location", ""),
                amenities=item.get("amenities", ""),
                check_in=item.get("check_in", ""),
                check_out=item.get("check_out", ""),
                listing_url=item.get("listing_url", ""),
                source=item.get("source", ""),
                raw_data=item,
            )
            unique.append(listing)
        except (ValueError, TypeError) as exc:
            LOGGER.warning("Skipping invalid hotel listing: %s", exc)

    return unique[:TARGET_LISTINGS]


# ---------------------------------------------------------------------------
# Top-level orchestrator
# ---------------------------------------------------------------------------

def search_hotels_natural(
    query: str,
) -> tuple[HotelSearchParams, list[HotelListing]]:
    """Parse natural language query and search for hotels."""
    params = parse_hotel_query(query)

    if not params.location:
        raise HotelSearchError(
            "Could not determine a location from your query. "
            "Please include a city or destination for the hotel search."
        )

    listings = search_hotels(params)
    return params, listings
