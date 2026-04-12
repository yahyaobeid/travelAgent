from django.urls import path

from . import views

app_name = "hotels"

urlpatterns = [
    path("", views.hotel_search, name="search"),
    path("<int:pk>/", views.hotel_results, name="detail"),
]
