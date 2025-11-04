import logging
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404, redirect, render

from .eventbrite import fetch_events
from .forms import ItineraryForm, ItineraryUpdateForm
from .models import Itinerary
from .services import ItineraryGenerationError, ItineraryRequest, generate_itinerary
from .utils import render_markdown

PENDING_SESSION_KEY = "pending_itinerary"

LOGGER = logging.getLogger(__name__)


def home(request):
    """Landing page listing recent itineraries."""
    itineraries = Itinerary.objects.filter(user=request.user) if request.user.is_authenticated else []
    return render(request, "core/home.html", {"itineraries": itineraries})


@login_required
def itinerary_detail(request, pk: int):
    """Display a generated itinerary."""
    itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)
    events = fetch_events(
        itinerary.destination,
        itinerary.start_date.strftime("%Y-%m-%d"),
        itinerary.end_date.strftime("%Y-%m-%d"),
    )
    return render(request, "core/itinerary_detail.html", {"itinerary": itinerary, "events": events})


def create_itinerary(request):
    """Collect trip details, call OpenAI, and persist the resulting itinerary."""
    if request.method == "POST":
        form = ItineraryForm(request.POST)
        action = request.POST.get("action", "preview")

        if action == "save" and not request.user.is_authenticated:
            form.add_error(None, "Please sign in to save itineraries to your account.")
        elif form.is_valid():
            itinerary = form.save(commit=False)
            LOGGER.info(
                "Create itinerary form submission by %s: %s",
                request.user if request.user.is_authenticated else "anonymous",
                {
                    "destination": itinerary.destination,
                    "start_date": itinerary.start_date,
                    "end_date": itinerary.end_date,
                    "interests": itinerary.interests,
                    "activities": itinerary.activities,
                    "food_preferences": itinerary.food_preferences,
                    "preference": itinerary.preference,
                    "action": action,
                },
            )
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
                form.add_error(None, str(exc))
            else:
                should_save = action == "save" or (request.user.is_authenticated and action == "preview")

                if should_save and request.user.is_authenticated:
                    itinerary.user = request.user
                    itinerary.prompt = prompt
                    itinerary.generated_plan = plan
                    itinerary.save()
                    messages.success(request, "Itinerary created successfully.")
                    return redirect("core:itinerary_detail", pk=itinerary.pk)

                events = fetch_events(
                    itinerary.destination,
                    itinerary.start_date.strftime("%Y-%m-%d"),
                    itinerary.end_date.strftime("%Y-%m-%d"),
                )
                if request.user.is_authenticated and should_save:
                    itinerary.events_cache = events  # temporary attribute for template use
                    return redirect("core:itinerary_detail", pk=itinerary.pk)

                request.session[PENDING_SESSION_KEY] = {
                    "destination": itinerary.destination,
                    "start_date": itinerary.start_date.strftime("%Y-%m-%d"),
                    "end_date": itinerary.end_date.strftime("%Y-%m-%d"),
                    "interests": itinerary.interests,
                    "activities": itinerary.activities,
                    "food_preferences": itinerary.food_preferences,
                    "preference": itinerary.preference,
                    "prompt": prompt,
                    "generated_plan": plan,
                    "events": events,
                }
                return redirect("core:itinerary_preview")
    else:
        form = ItineraryForm()

    return render(request, "core/itinerary_form.html", {"form": form, "is_edit": False})


@login_required
def edit_itinerary(request, pk: int):
    """Allow users to tweak itinerary details and optionally regenerate the plan."""
    itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)

    if request.method == "POST":
        form = ItineraryUpdateForm(request.POST, instance=itinerary)
        if form.is_valid():
            regenerate = form.cleaned_data.get("regenerate_plan", False)
            updated_itinerary = form.save(commit=False)
            LOGGER.info(
                "Edit itinerary submission by %s (itinerary %s): %s",
                request.user,
                itinerary.pk,
                {
                    "destination": updated_itinerary.destination,
                    "start_date": updated_itinerary.start_date,
                    "end_date": updated_itinerary.end_date,
                    "interests": updated_itinerary.interests,
                    "activities": updated_itinerary.activities,
                    "food_preferences": updated_itinerary.food_preferences,
                    "preference": updated_itinerary.preference,
                    "regenerate_plan": regenerate,
                },
            )
            if regenerate:
                payload = ItineraryRequest(
                    destination=updated_itinerary.destination,
                    start_date=updated_itinerary.start_date.strftime("%Y-%m-%d"),
                    end_date=updated_itinerary.end_date.strftime("%Y-%m-%d"),
                    interests=updated_itinerary.interests,
                    activities=updated_itinerary.activities,
                    food_preferences=updated_itinerary.food_preferences,
                    preference=updated_itinerary.preference,
                )
                try:
                    prompt, plan = generate_itinerary(payload)
                except (ImproperlyConfigured, ItineraryGenerationError) as exc:
                    form.add_error(None, str(exc))
                    return render(
                        request,
                        "core/itinerary_form.html",
                        {"form": form, "itinerary": itinerary, "is_edit": True},
                    )
                else:
                    updated_itinerary.prompt = prompt
                    updated_itinerary.generated_plan = plan
            updated_itinerary.save()
            messages.success(request, "Itinerary updated successfully.")
            return redirect("core:itinerary_detail", pk=updated_itinerary.pk)
    else:
        form = ItineraryUpdateForm(instance=itinerary)

    return render(
        request,
        "core/itinerary_form.html",
        {"form": form, "itinerary": itinerary, "is_edit": True},
    )


@login_required
def delete_itinerary(request, pk: int):
    """Allow a user to delete their itinerary after confirmation."""
    itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)

    if request.method == "POST":
        itinerary.delete()
        messages.success(request, "Itinerary deleted successfully.")
        return redirect("core:home")

    return render(
        request,
        "core/itinerary_confirm_delete.html",
        {"itinerary": itinerary},
    )


def preview_itinerary(request):
    """Display the most recently generated itinerary without hitting the API again."""
    pending = request.session.get(PENDING_SESSION_KEY)
    if not pending:
        messages.error(request, "Generate a new itinerary to see a preview.")
        return redirect("core:itinerary_new")

    context = {
        "destination": pending["destination"],
        "start_date": date.fromisoformat(pending["start_date"]),
        "end_date": date.fromisoformat(pending["end_date"]),
        "interests": pending.get("interests"),
        "activities": pending.get("activities"),
        "food_preferences": pending.get("food_preferences"),
        "preference": dict(Itinerary.STYLE_CHOICES).get(pending.get("preference"), "Balanced"),
        "generated_plan": render_markdown(pending["generated_plan"]),
        "events": pending.get("events", []),
    }
    LOGGER.info("Preview itinerary context for %s: %s", request.user if request.user.is_authenticated else "anonymous", context)
    return render(request, "core/itinerary_preview.html", context)


@login_required
def save_pending_itinerary(request):
    """Persist a previously previewed itinerary after the user signs in."""
    pending = request.session.get(PENDING_SESSION_KEY)
    if not pending:
        messages.error(request, "We couldn't find a pending itinerary to save. Please generate a new one.")
        return redirect("core:itinerary_new")

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
    LOGGER.info("Saved pending itinerary for %s: %s", request.user, itinerary.pk)
    request.session.pop(PENDING_SESSION_KEY, None)
    messages.success(request, "Itinerary saved to your trips.")
    return redirect("core:itinerary_detail", pk=itinerary.pk)
