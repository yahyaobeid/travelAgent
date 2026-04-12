"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.conf import settings
from django.http import HttpResponse
from django.urls import include, path, re_path

def react_app(request, *args, **kwargs):
    """Serve the React SPA index.html for all non-API, non-admin paths."""
    index_path = getattr(settings, "REACT_INDEX_HTML", None)
    if index_path and index_path.exists():
        return HttpResponse(index_path.read_text(), content_type="text/html")
    # Fallback: still serve Django templates during development
    from django.shortcuts import redirect
    return redirect("/")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("api.urls")),
    # Legacy Django template routes (kept during migration)
    path("", include("core.urls")),
    path("itineraries/", include("itinerary.urls")),
    path("flights/", include("flights.urls")),
    path("cars/", include("cars.urls")),
    path("hotels/", include("hotels.urls")),
    path("users/", include("users.urls")),
]
