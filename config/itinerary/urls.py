from django.urls import path

from . import views

app_name = "itinerary"

urlpatterns = [
    path("new/", views.create_itinerary, name="new"),
    path("preview/", views.preview_itinerary, name="preview"),
    path("save-pending/", views.save_pending_itinerary, name="save_pending"),
    path("<int:pk>/", views.itinerary_detail, name="detail"),
    path("<int:pk>/edit/", views.edit_itinerary, name="edit"),
    path("<int:pk>/delete/", views.delete_itinerary, name="delete"),
]
