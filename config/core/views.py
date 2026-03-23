from django.shortcuts import render

from itinerary.models import Itinerary


def home(request):
    """Landing page listing recent itineraries for the authenticated user."""
    itineraries = Itinerary.objects.filter(user=request.user) if request.user.is_authenticated else []
    return render(request, "core/home.html", {"itineraries": itineraries})
