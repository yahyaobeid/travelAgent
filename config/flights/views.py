import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import FlightSearch
from .nl_search import FlightSearchError, run_workflow_sync

LOGGER = logging.getLogger(__name__)

FLIGHT_SESSION_KEY = "flight_search_results"
FLIGHT_HISTORY_KEY = "flight_chat_history"


def search(request):
    """Unified flight chat — GET renders the page, POST handles AJAX messages."""
    if request.method == "POST":
        query_text = request.POST.get("query", "").strip()

        if not query_text:
            return JsonResponse({"error": "Please enter a search query."}, status=400)

        history = request.session.get(FLIGHT_HISTORY_KEY, [])

        try:
            agent_output, updated_history = run_workflow_sync(query_text, history)
        except FlightSearchError as exc:
            return JsonResponse({"error": str(exc)}, status=500)

        LOGGER.info(
            "Flight search by %s: %s",
            request.user if request.user.is_authenticated else "anonymous",
            query_text,
        )

        # Detect if the agent called search_google_flights
        is_tool_call = False
        try:
            parsed = json.loads(agent_output)
            is_tool_call = isinstance(parsed, dict) and parsed.get("tool") == "search_google_flights"
        except (json.JSONDecodeError, ValueError):
            pass

        # Persist raw agent history
        request.session[FLIGHT_HISTORY_KEY] = updated_history

        # Append to display history
        display_history = request.session.get(FLIGHT_SESSION_KEY, {}).get("display_history", [])
        display_history = display_history + [
            {"role": "user", "text": query_text},
            {"role": "agent", "text": agent_output, "is_tool_call": is_tool_call},
        ]
        request.session[FLIGHT_SESSION_KEY] = {"display_history": display_history}
        request.session.modified = True

        return JsonResponse({"text": agent_output, "is_tool_call": is_tool_call})

    # GET — clear history on a fresh visit (no ?continue param)
    if not request.GET.get("continue"):
        request.session.pop(FLIGHT_HISTORY_KEY, None)
        request.session.pop(FLIGHT_SESSION_KEY, None)
        display_history = []
    else:
        payload = request.session.get(FLIGHT_SESSION_KEY)
        display_history = payload.get("display_history", []) if payload else []

    return render(request, "flights/search.html", {"display_history": display_history})


def results(request):
    """Legacy redirect — conversation now lives at /flights/."""
    return redirect("flights:search")


@login_required
def detail(request, pk: int):
    """Display saved flight search results for authenticated users."""
    search_obj = get_object_or_404(FlightSearch, pk=pk, user=request.user)
    db_results = search_obj.results.all()

    return render(request, "flights/nl_results.html", {
        "search": search_obj,
        "results": db_results,
    })
