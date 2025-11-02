from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("itineraries/new/", views.create_itinerary, name="itinerary_new"),
    path("itineraries/<int:pk>/", views.itinerary_detail, name="itinerary_detail"),
    path("itineraries/<int:pk>/edit/", views.edit_itinerary, name="itinerary_edit"),
    path("itineraries/<int:pk>/delete/", views.delete_itinerary, name="itinerary_delete"),
]
