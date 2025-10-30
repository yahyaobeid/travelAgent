from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ItineraryForm
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

    return render(request, "core/itinerary_form.html", {"form": form})
