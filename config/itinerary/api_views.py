import logging
from datetime import date

from django.core.exceptions import ImproperlyConfigured
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .eventbrite import fetch_events
from .models import Itinerary
from .serializers import ItineraryCreateSerializer, ItinerarySerializer, ItineraryUpdateSerializer
from .services import ItineraryGenerationError, ItineraryRequest, generate_itinerary

LOGGER = logging.getLogger(__name__)
PENDING_SESSION_KEY = "pending_itinerary"


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def itinerary_list(request):
    qs = Itinerary.objects.filter(user=request.user)
    return Response(ItinerarySerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def itinerary_create(request):
    serializer = ItineraryCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    action = data["action"]

    if action == "save" and not request.user.is_authenticated:
        return Response(
            {"error": "Please sign in to save itineraries to your account."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    payload = ItineraryRequest(
        destination=data["destination"],
        start_date=data["start_date"].strftime("%Y-%m-%d"),
        end_date=data["end_date"].strftime("%Y-%m-%d"),
        interests=data["interests"],
        activities=data["activities"],
        food_preferences=data["food_preferences"],
        preference=data["preference"],
    )

    try:
        prompt, plan = generate_itinerary(payload)
    except (ImproperlyConfigured, ItineraryGenerationError) as exc:
        return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    should_save = action == "save" or request.user.is_authenticated

    if should_save and request.user.is_authenticated:
        itinerary = Itinerary.objects.create(
            user=request.user,
            destination=data["destination"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            interests=data["interests"],
            activities=data["activities"],
            food_preferences=data["food_preferences"],
            preference=data["preference"],
            prompt=prompt,
            generated_plan=plan,
        )
        LOGGER.info("Created itinerary %s for %s", itinerary.pk, request.user)
        return Response(ItinerarySerializer(itinerary).data, status=status.HTTP_201_CREATED)

    # Anonymous preview — store in session
    events = fetch_events(
        data["destination"],
        data["start_date"].strftime("%Y-%m-%d"),
        data["end_date"].strftime("%Y-%m-%d"),
    )
    request.session[PENDING_SESSION_KEY] = {
        "destination": data["destination"],
        "start_date": data["start_date"].strftime("%Y-%m-%d"),
        "end_date": data["end_date"].strftime("%Y-%m-%d"),
        "interests": data["interests"],
        "activities": data["activities"],
        "food_preferences": data["food_preferences"],
        "preference": data["preference"],
        "prompt": prompt,
        "generated_plan": plan,
        "events": events,
    }
    return Response(
        {
            "preview": True,
            "destination": data["destination"],
            "start_date": data["start_date"].strftime("%Y-%m-%d"),
            "end_date": data["end_date"].strftime("%Y-%m-%d"),
            "generated_plan": plan,
            "events": events,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def itinerary_preview(request):
    pending = request.session.get(PENDING_SESSION_KEY)
    if not pending:
        return Response({"error": "No pending itinerary found."}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        "destination": pending["destination"],
        "start_date": pending["start_date"],
        "end_date": pending["end_date"],
        "interests": pending.get("interests", ""),
        "activities": pending.get("activities", ""),
        "food_preferences": pending.get("food_preferences", ""),
        "preference": pending.get("preference", Itinerary.STYLE_GENERAL),
        "style_label": dict(Itinerary.STYLE_CHOICES).get(pending.get("preference"), "Balanced"),
        "generated_plan": pending["generated_plan"],
        "events": pending.get("events", []),
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def itinerary_save_pending(request):
    pending = request.session.get(PENDING_SESSION_KEY)
    if not pending:
        return Response(
            {"error": "No pending itinerary found. Please generate a new one."},
            status=status.HTTP_404_NOT_FOUND,
        )

    itinerary = Itinerary.objects.create(
        user=request.user,
        destination=pending["destination"],
        start_date=date.fromisoformat(pending["start_date"]),
        end_date=date.fromisoformat(pending["end_date"]),
        interests=pending.get("interests", ""),
        activities=pending.get("activities", ""),
        food_preferences=pending.get("food_preferences", ""),
        preference=pending.get("preference", Itinerary.STYLE_GENERAL),
        prompt=pending["prompt"],
        generated_plan=pending["generated_plan"],
    )
    request.session.pop(PENDING_SESSION_KEY, None)
    LOGGER.info("Saved pending itinerary %s for %s", itinerary.pk, request.user)
    return Response(ItinerarySerializer(itinerary).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def itinerary_detail(request, pk: int):
    try:
        itinerary = Itinerary.objects.get(pk=pk, user=request.user)
    except Itinerary.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        events = fetch_events(
            itinerary.destination,
            itinerary.start_date.strftime("%Y-%m-%d"),
            itinerary.end_date.strftime("%Y-%m-%d"),
        )
        return Response({"itinerary": ItinerarySerializer(itinerary).data, "events": events})

    if request.method == "PUT":
        serializer = ItineraryUpdateSerializer(itinerary, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        regenerate = serializer.validated_data.pop("regenerate_plan", False)

        if regenerate:
            updated = serializer.save(commit=False) if hasattr(serializer, "save") else None
            # Apply partial updates manually so we can regenerate
            for attr, value in serializer.validated_data.items():
                setattr(itinerary, attr, value)

            payload = ItineraryRequest(
                destination=itinerary.destination,
                start_date=itinerary.start_date.strftime("%Y-%m-%d"),
                end_date=itinerary.end_date.strftime("%Y-%m-%d"),
                interests=itinerary.interests,
                activities=itinerary.activities,
                food_preferences=itinerary.food_preferences,
                preference=itinerary.preference,
            )
            try:
                prompt, plan = generate_itinerary(payload)
            except (ImproperlyConfigured, ItineraryGenerationError) as exc:
                return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            itinerary.prompt = prompt
            itinerary.generated_plan = plan
            itinerary.save()
        else:
            serializer.save()
            itinerary.refresh_from_db()

        return Response(ItinerarySerializer(itinerary).data)

    # DELETE
    itinerary.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
