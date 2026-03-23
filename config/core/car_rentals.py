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
SEARCH_PAUSE = 1.5  # seconds between Google searches to avoid rate-limiting

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CarRentalSearchParams:
    location: str
    car_type: str = ""
    max_price_per_day: float | None = None
    pickup_date: str = ""
    dropoff_date: str = ""


@dataclass
class CarRentalListing:
    car_name: str
    car_type: str
    price_per_day: float
    price_display: str
    rental_company: str
    location: str
    availability: str
    listing_url: str
    source: str
    raw_data: dict = field(default_factory=dict)


class CarRentalSearchError(Exception):
    """Raised when car rental search fails."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_anthropic_client():
    api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
    if not api_key:
        raise ImproperlyConfigured("ANTHROPIC_API_KEY is not configured.")
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise CarRentalSearchError(
            "Anthropic SDK is not installed. Add 'anthropic' to your dependencies."
        ) from exc
    return Anthropic(api_key=api_key)


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
# Tool definitions for Claude
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "search_google",
        "description": (
            "Search Google for car rental listings. Returns a list of top result "
            "URLs and snippets. Use specific queries including location, car type, "
            "and dates to find relevant rental pages."
        ),
        "input_schema": {
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
    {
        "name": "scrape_page",
        "description": (
            "Fetch a web page and return its cleaned text content. Use this to "
            "read the content of car rental listing pages found via search."
        ),
        "input_schema": {
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
    {
        "name": "extract_car_listings",
        "description": (
            "Extract structured car rental listing data from raw page text. "
            "Returns a JSON array of car rental objects with price, car details, "
            "and links. Use this after scraping a page to get structured data."
        ),
        "input_schema": {
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
]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _tool_search_google(query: str) -> list[dict]:
    """Search Google and return top results."""
    try:
        from googlesearch import search as gsearch
    except ImportError as exc:
        raise CarRentalSearchError(
            "googlesearch-python is not installed."
        ) from exc

    LOGGER.info("Google search: %s", query)
    results = []
    try:
        for url in gsearch(query, num_results=10):
            results.append({
                "url": url,
                "title": "",
                "snippet": "",
            })
            time.sleep(0.2)  # small pause between result fetches
    except Exception as exc:
        LOGGER.warning("Google search error: %s", exc)
        return [{"error": f"Search failed: {exc}"}]

    time.sleep(SEARCH_PAUSE)
    return results


def _tool_scrape_page(url: str) -> str:
    """Fetch and parse a web page, returning cleaned text."""
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

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    return text[:SCRAPE_MAX_CHARS]


def _tool_extract_car_listings(
    raw_text: str, source_url: str, client, model: str
) -> list[dict]:
    """Use Claude to extract structured car listings from raw page text."""
    domain = urlparse(source_url).netloc

    system_prompt = (
        "You are a data extraction assistant. Extract car rental listing information "
        "from the provided text. Return ONLY a JSON array of objects. Each object must have:\n"
        '- "car_name": string (e.g. "Toyota Camry 2023")\n'
        '- "car_type": string (e.g. "Sedan", "SUV", "Compact", "Minivan")\n'
        '- "price_per_day": number (USD, e.g. 65.0)\n'
        '- "price_display": string (e.g. "$65/day")\n'
        '- "rental_company": string (e.g. "Enterprise", "Hertz")\n'
        '- "location": string (pickup location)\n'
        '- "availability": string (dates or "Available" if not specified)\n'
        '- "listing_url": string (direct link if found in text, otherwise "")\n'
        f'- "source": "{domain}"\n\n'
        "If you cannot extract valid listings from the text, return an empty array [].\n"
        "Return ONLY the JSON array, no other text."
    )

    try:
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": raw_text[:SCRAPE_MAX_CHARS]}],
        )
    except Exception as exc:
        LOGGER.warning("Extract listings failed: %s", exc)
        return []

    result_text = ""
    for block in response.content:
        if block.type == "text":
            result_text += block.text

    try:
        listings = _extract_json_array(result_text)
    except (ValueError, json.JSONDecodeError):
        LOGGER.warning("Could not parse extracted listings JSON")
        return []

    # Validate each listing has required fields
    valid = []
    for item in listings:
        if not isinstance(item, dict):
            continue
        if item.get("car_name") and item.get("price_per_day"):
            # Ensure source and listing_url are populated
            item.setdefault("source", domain)
            item.setdefault("listing_url", source_url)
            item.setdefault("availability", "")
            item.setdefault("location", "")
            item.setdefault("rental_company", "")
            item.setdefault("car_type", "")
            item.setdefault("price_display", f"${item['price_per_day']}/day")
            valid.append(item)

    return valid


# ---------------------------------------------------------------------------
# Dispatch tool calls
# ---------------------------------------------------------------------------

def _dispatch_tool(name: str, input_data: dict, client, model: str):
    """Execute a tool call and return the result as a string."""
    if name == "search_google":
        results = _tool_search_google(input_data["query"])
        return json.dumps(results)
    elif name == "scrape_page":
        return _tool_scrape_page(input_data["url"])
    elif name == "extract_car_listings":
        listings = _tool_extract_car_listings(
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

def parse_car_rental_query(query: str) -> CarRentalSearchParams:
    """Use Claude to extract structured car rental params from natural language."""
    client = _get_anthropic_client()
    model = getattr(settings, "ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    today = date.today().isoformat()

    system_prompt = (
        "You are a car rental search assistant. Extract search parameters from the user's query.\n"
        "Return ONLY a JSON object with these keys:\n"
        '- "location": string (city or area, e.g. "Miami, FL")\n'
        '- "car_type": string (e.g. "SUV", "Sedan", "Compact", "Minivan", or "" if not specified)\n'
        '- "max_price_per_day": number or null (USD budget per day)\n'
        '- "pickup_date": string (YYYY-MM-DD) or ""\n'
        '- "dropoff_date": string (YYYY-MM-DD) or ""\n\n'
        f"Today's date is {today}. Resolve relative dates (e.g. 'next weekend') accordingly.\n"
        "Return ONLY the JSON object, no other text."
    )

    LOGGER.info("Parsing car rental query: %s", query)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": query}],
        )
    except Exception as exc:
        raise CarRentalSearchError(f"Failed to parse car rental query: {exc}") from exc

    raw_text = ""
    for block in response.content:
        if block.type == "text":
            raw_text += block.text

    LOGGER.info("Parse response: %s", raw_text)

    try:
        data = _extract_json_object(raw_text)
    except (ValueError, json.JSONDecodeError) as exc:
        raise CarRentalSearchError(
            f"Could not parse car rental parameters: {exc}"
        ) from exc

    max_price = data.get("max_price_per_day")
    if max_price is not None:
        try:
            max_price = float(max_price)
        except (ValueError, TypeError):
            max_price = None

    return CarRentalSearchParams(
        location=data.get("location", ""),
        car_type=data.get("car_type", ""),
        max_price_per_day=max_price,
        pickup_date=data.get("pickup_date", ""),
        dropoff_date=data.get("dropoff_date", ""),
    )


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

def search_car_rentals(params: CarRentalSearchParams) -> list[CarRentalListing]:
    """Run the Claude agent loop to find car rental listings."""
    client = _get_anthropic_client()
    model = getattr(settings, "ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    system_prompt = (
        "You are a car rental search agent. Your goal is to find exactly 20 car rental "
        "listings matching the user's criteria.\n\n"
        "Strategy:\n"
        "1. Use search_google to find car rental pages (try sites like Kayak, Expedia, "
        "Priceline, Rentalcars.com, Turo, Enterprise, Hertz, Budget, etc.)\n"
        "2. Use scrape_page to fetch promising result pages\n"
        "3. Use extract_car_listings to pull structured data from the scraped content\n"
        "4. Keep searching and scraping until you have accumulated 20 listings\n"
        "5. If a page fails to scrape or yields no results, try the next one\n"
        "6. Vary your search queries to cover different rental companies and aggregators\n\n"
        "Important: Call tools one step at a time. Search first, then scrape results, "
        "then extract listings. Repeat until you have enough listings."
    )

    # Build user message from params
    parts = [f"Find car rentals in {params.location}."]
    if params.car_type:
        parts.append(f"Car type: {params.car_type}.")
    if params.max_price_per_day:
        parts.append(f"Budget: under ${params.max_price_per_day}/day.")
    if params.pickup_date:
        parts.append(f"Pickup date: {params.pickup_date}.")
    if params.dropoff_date:
        parts.append(f"Dropoff date: {params.dropoff_date}.")
    parts.append(f"Find {TARGET_LISTINGS} car rental listings with prices and details.")

    user_message = " ".join(parts)
    LOGGER.info("Agent user message: %s", user_message)

    messages = [{"role": "user", "content": user_message}]
    all_listings: list[dict] = []

    for iteration in range(MAX_AGENT_ITERATIONS):
        LOGGER.info("Agent iteration %d, listings so far: %d", iteration + 1, len(all_listings))

        try:
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=TOOLS,
            )
        except Exception as exc:
            LOGGER.error("Agent API call failed: %s", exc)
            break

        # Build assistant message content for conversation history
        assistant_content = []
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                assistant_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
                tool_calls.append(block)

        messages.append({"role": "assistant", "content": assistant_content})

        # If no tool calls, the agent decided to stop
        if not tool_calls:
            LOGGER.info("Agent stopped (no tool calls)")
            break

        # Execute each tool call and build results
        tool_results = []
        for tc in tool_calls:
            LOGGER.info("Tool call: %s(%s)", tc.name, json.dumps(tc.input)[:200])
            result_str = _dispatch_tool(tc.name, tc.input, client, model)

            # If this was an extract call, accumulate listings
            if tc.name == "extract_car_listings":
                try:
                    extracted = json.loads(result_str)
                    if isinstance(extracted, list):
                        all_listings.extend(extracted)
                        LOGGER.info("Extracted %d listings (total: %d)", len(extracted), len(all_listings))
                except (json.JSONDecodeError, TypeError):
                    pass

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": result_str[:SCRAPE_MAX_CHARS],
            })

        messages.append({"role": "user", "content": tool_results})

        if len(all_listings) >= TARGET_LISTINGS:
            LOGGER.info("Reached target of %d listings", TARGET_LISTINGS)
            break

    # Deduplicate by (car_name, rental_company, price_per_day)
    seen = set()
    unique: list[CarRentalListing] = []
    for item in all_listings:
        key = (
            item.get("car_name", ""),
            item.get("rental_company", ""),
            item.get("price_per_day", 0),
        )
        if key in seen:
            continue
        seen.add(key)
        try:
            listing = CarRentalListing(
                car_name=item.get("car_name", "Unknown"),
                car_type=item.get("car_type", ""),
                price_per_day=float(item.get("price_per_day", 0)),
                price_display=item.get("price_display", ""),
                rental_company=item.get("rental_company", ""),
                location=item.get("location", ""),
                availability=item.get("availability", ""),
                listing_url=item.get("listing_url", ""),
                source=item.get("source", ""),
                raw_data=item,
            )
            unique.append(listing)
        except (ValueError, TypeError) as exc:
            LOGGER.warning("Skipping invalid listing: %s", exc)

    return unique[:TARGET_LISTINGS]


# ---------------------------------------------------------------------------
# Top-level orchestrator
# ---------------------------------------------------------------------------

def search_car_rentals_natural(
    query: str,
) -> tuple[CarRentalSearchParams, list[CarRentalListing]]:
    """Parse natural language query and search for car rentals."""
    params = parse_car_rental_query(query)

    if not params.location:
        raise CarRentalSearchError(
            "Could not determine a location from your query. "
            "Please include a city or area for the car rental."
        )

    listings = search_car_rentals(params)
    return params, listings
