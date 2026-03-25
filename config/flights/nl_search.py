from __future__ import annotations

import asyncio
import json
import logging
import os

import serpapi
from agents import Agent, ModelSettings, RunConfig, Runner, TResponseInputItem, function_tool, trace
from pydantic import BaseModel
from datetime import date

LOGGER = logging.getLogger(__name__)

_CABIN_MAP = {
    "economy": 1,
    "premium_economy": 2,
    "premium economy": 2,
    "business": 3,
    "first": 4,
}

_SORT_MAP = {
    "best": 1,
    "top": 1,
    "cheapest": 2,
    "price": 2,
    "fastest": 3,
    "duration": 3,
    "emissions": 4,
}


class FlightSearchError(Exception):
    """Raised when flight search fails."""


@function_tool
def search_google_flights(
    origin: str,
    destination: str,
    depart_date: str,
    return_date: str = "",
    passengers: int = 1,
    cabin: str = "economy",
    max_stops: int = 1,
    bags: int = 0,
    sort_by: str = "best",
) -> str:
    api_key = os.environ.get("SERPAPI_API_KEY", "")
    if not api_key:
        return json.dumps({"error": "SERPAPI_API_KEY not configured"})

    params: dict = {
        "engine": "google_flights",
        "hl": "en",
        "gl": "us",
        "departure_id": origin.upper(),
        "arrival_id": destination.upper(),
        "outbound_date": depart_date,
        "currency": "USD",
        "adults": str(passengers) if passengers else "1",
    }

    if return_date:
        params["return_date"] = return_date

    if cabin:
        params["travel_class"] = str(_CABIN_MAP.get(cabin.lower(), 1))

    if max_stops is not None and max_stops >= 0:
        # SerpAPI: 0=any, 1=nonstop, 2=≤1 stop, 3=≤2 stops
        params["stops"] = str(min(max_stops + 1, 3)) if max_stops <= 2 else "0"

    if bags:
        params["bags"] = str(bags)

    if sort_by:
        params["sort_by"] = str(_SORT_MAP.get(sort_by.lower(), 1))

    LOGGER.info("SerpAPI call params: %s", params)
    try:
        client = serpapi.Client(api_key=api_key)
        results = client.search(params)
        results_dict = dict(results) if not isinstance(results, dict) else results
        LOGGER.info("SerpAPI response keys: %s", list(results_dict.keys()))
        error_info = results_dict.get("error")
        if error_info:
            LOGGER.error("SerpAPI returned error: %s", error_info)
            return json.dumps({"error": error_info})
        output = {
            "best_flights": results_dict.get("best_flights", [])[:5],
            "other_flights": results_dict.get("other_flights", [])[:5],
            "price_insights": results_dict.get("price_insights"),
        }
        return json.dumps(output, indent=2)
    except Exception as exc:
        LOGGER.exception("SerpAPI call failed: %s", exc)
        return json.dumps({"error": str(exc)})


search_flights_agent = Agent(
    name="Search Flights",
    instructions=f"""You are an AI flight search agent.

Your job is to help users find the best flights based on their preferences using real-time data.

You have access to a tool called `search_google_flights` that retrieves flight results.

BEHAVIOR RULES:

1. Always collect required inputs before calling the tool:
   - origin (IATA code)
   - destination (IATA code)
   - depart_date

2. If any required info is missing, ask a follow-up question instead of guessing.

3. Optional preferences to gather if not provided:
   - return date
   - number of passengers
   - cabin class
   - baggage
   - maximum stops
   - budget or preference (cheapest, fastest, best)

4. NEVER invent flight data, prices, or airlines.
   Always call the tool for real results.

5. After receiving tool results:
   - Identify:
     • Best overall flight
     • Cheapest flight
     • Fastest flight
   - Provide 3–5 strong options total.

6. Format your response clearly:
   - Airline
   - Price
   - Departure/arrival times
   - Duration
   - Stops
   - Why it's recommended

7. Be concise but helpful. Do not overwhelm the user.

8. If results are limited or uncertain, say so.

9. Do NOT say you are calling a tool.
   Just behave naturally.

10. Do NOT perform bookings or claim tickets are reserved.

11. Today's date is {date.today().isoformat()}. When a user provides dates without a year, assume the current year ({date.today().year}).

Your goal is to act like a smart travel assistant that helps users compare and choose flights.""",
    model="gpt-4o-mini",
    tools=[search_google_flights],
    model_settings=ModelSettings(
        temperature=0.2,
        top_p=1,
        parallel_tool_calls=True,
        max_tokens=3001,
        store=True,
    ),
)


class WorkflowInput(BaseModel):
    input_as_text: str


async def run_workflow(workflow_input: WorkflowInput, history: list | None = None) -> dict:
    with trace("New workflow"):
        prior: list[TResponseInputItem] = history or []

        new_user_message: TResponseInputItem = {
            "role": "user",
            "content": [{"type": "input_text", "text": workflow_input.input_as_text}],
        }

        conversation = [*prior, new_user_message]

        result = await Runner.run(
            search_flights_agent,
            input=conversation,
            run_config=RunConfig(
                trace_metadata={
                    "__trace_source__": "agent-builder",
                    "workflow_id": "wf_69091035bc8c8190b51c94255614637d05fae5ba42c15bad",
                }
            ),
        )
        for item in result.new_items:
            LOGGER.info("Item type: %s | content: %s", type(item).__name__, item)

        # Build updated history: everything sent + everything the agent produced
        updated_history = conversation + [item.to_input_item() for item in result.new_items]

        return {"output_text": result.final_output_as(str), "history": updated_history}


def run_workflow_sync(query: str, history: list | None = None) -> tuple[str, list]:
    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(
            run_workflow(WorkflowInput(input_as_text=query), history)
        )
        return result["output_text"], result["history"]
    except Exception as exc:
        raise FlightSearchError(f"Flight search failed: {exc}") from exc
    finally:
        loop.close()
