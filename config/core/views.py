from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ItineraryForm, ItineraryUpdateForm
from .models import Itinerary
from .services import ItineraryGenerationError, ItineraryRequest, generate_itinerary


@login_required
def home(request):
    """Landing page listing recent itineraries."""
    itineraries = Itinerary.objects.filter(user=request.user)
    return render(request, "core/home.html", {"itineraries": itineraries})


@login_required
def itinerary_detail(request, pk: int):
    """Display a generated itinerary."""
    itinerary = get_object_or_404(Itinerary, pk=pk, user=request.user)
    return render(request, "core/itinerary_detail.html", {"itinerary": itinerary})


@login_required
def create_itinerary(request):
    """Collect trip details, call OpenAI, and persist the resulting itinerary."""
    if request.method == "POST":
        form = ItineraryForm(request.POST)
        if form.is_valid():
            itinerary = form.save(commit=False)
            payload = ItineraryRequest(
                destination=itinerary.destination,
                start_date=itinerary.start_date.strftime("%Y-%m-%d"),
                end_date=itinerary.end_date.strftime("%Y-%m-%d"),
                interests=itinerary.interests,
                preference=itinerary.preference,
            )
            try:
                prompt, plan = generate_itinerary(payload)
            except (ImproperlyConfigured, ItineraryGenerationError) as exc:
                form.add_error(None, str(exc))
            else:
                itinerary.user = request.user
                itinerary.prompt = prompt
                itinerary.generated_plan = plan
                itinerary.save()
                messages.success(request, "Itinerary created successfully.")
                return redirect("core:itinerary_detail", pk=itinerary.pk)
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
            if regenerate:
                payload = ItineraryRequest(
                    destination=updated_itinerary.destination,
                    start_date=updated_itinerary.start_date.strftime("%Y-%m-%d"),
                    end_date=updated_itinerary.end_date.strftime("%Y-%m-%d"),
                    interests=updated_itinerary.interests,
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
