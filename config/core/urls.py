from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("itineraries/new/", views.create_itinerary, name="itinerary_new"),
    path("itineraries/<int:pk>/", views.itinerary_detail, name="itinerary_detail"),
]
