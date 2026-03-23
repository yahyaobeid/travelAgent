from django.urls import path

from . import views

app_name = "cars"

urlpatterns = [
    path("", views.car_rental_search, name="search"),
    path("<int:pk>/", views.car_rental_results, name="detail"),
    path("api/", views.car_rental_search_api, name="api_search"),
]
