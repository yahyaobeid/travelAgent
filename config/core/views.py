from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    """Landing page with quick links for authenticated users."""
    return render(request, "core/home.html")
