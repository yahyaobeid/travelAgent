import json
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import FlightSearch, FlightResult
from .nl_search import FlightSearchError, run_workflow_sync

LOGGER = logging.getLogger(__name__)

FLIGHT_SESSION_KEY = "flight_search_results"
FLIGHT_HISTORY_KEY = "flight_chat_history"


@api_view(["GET", "POST", "DELETE"])
@permission_classes([AllowAny])
def flight_chat(request):
    if request.method == "POST":
        query_text = request.data.get("query", "").strip()
        if not query_text:
            return Response({"error": "Please enter a search query."}, status=status.HTTP_400_BAD_REQUEST)

        history = request.session.get(FLIGHT_HISTORY_KEY, [])

        try:
            agent_output, updated_history = run_workflow_sync(query_text, history)
        except FlightSearchError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        LOGGER.info("Flight chat by %s: %s", request.user if request.user.is_authenticated else "anonymous", query_text)

        is_tool_call = False
        try:
            parsed = json.loads(agent_output)
            is_tool_call = isinstance(parsed, dict) and parsed.get("tool") == "search_google_flights"
        except (json.JSONDecodeError, ValueError):
            pass

        request.session[FLIGHT_HISTORY_KEY] = updated_history

        display_history = request.session.get(FLIGHT_SESSION_KEY, {}).get("display_history", [])
        display_history = display_history + [
            {"role": "user", "text": query_text},
            {"role": "agent", "text": agent_output, "is_tool_call": is_tool_call},
        ]
        request.session[FLIGHT_SESSION_KEY] = {"display_history": display_history}
        request.session.modified = True

        return Response({"text": agent_output, "is_tool_call": is_tool_call})

    if request.method == "GET":
        payload = request.session.get(FLIGHT_SESSION_KEY)
        display_history = payload.get("display_history", []) if payload else []
        return Response({"display_history": display_history})

    # DELETE — clear history
    request.session.pop(FLIGHT_HISTORY_KEY, None)
    request.session.pop(FLIGHT_SESSION_KEY, None)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def flight_detail(request, pk: int):
    try:
        search_obj = FlightSearch.objects.get(pk=pk, user=request.user)
    except FlightSearch.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    results = list(search_obj.results.values(
        "id", "airline", "flight_number", "departure_time", "arrival_time",
        "duration", "stops", "price_cents", "currency", "booking_url",
    ))
    return Response({
        "search": {
            "id": search_obj.pk,
            "natural_query": search_obj.natural_query,
            "origin_airport": search_obj.origin_airport,
            "destination_airport": search_obj.destination_airport,
            "departure_date": search_obj.departure_date,
            "return_date": search_obj.return_date,
            "passengers": search_obj.passengers,
            "cabin_class": search_obj.cabin_class,
        },
        "results": results,
    })
