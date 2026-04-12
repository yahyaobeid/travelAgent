from django.urls import path, include

from . import auth_views
from itinerary import api_views as itinerary_api
from flights import api_views as flights_api
from cars import api_views as cars_api
from hotels import api_views as hotels_api

urlpatterns = [
    # CSRF cookie endpoint — must be called before the first authenticated POST
    path("csrf/", auth_views.csrf_token_view, name="api_csrf"),

    # Auth
    path("auth/login/", auth_views.login_view, name="api_login"),
    path("auth/register/", auth_views.register_view, name="api_register"),
    path("auth/logout/", auth_views.logout_view, name="api_logout"),
    path("auth/me/", auth_views.me_view, name="api_me"),

    # Itineraries
    path("itineraries/", itinerary_api.itinerary_list, name="api_itinerary_list"),
    path("itineraries/create/", itinerary_api.itinerary_create, name="api_itinerary_create"),
    path("itineraries/preview/", itinerary_api.itinerary_preview, name="api_itinerary_preview"),
    path("itineraries/save-pending/", itinerary_api.itinerary_save_pending, name="api_itinerary_save_pending"),
    path("itineraries/<int:pk>/", itinerary_api.itinerary_detail, name="api_itinerary_detail"),

    # Flights
    path("flights/chat/", flights_api.flight_chat, name="api_flight_chat"),
    path("flights/<int:pk>/", flights_api.flight_detail, name="api_flight_detail"),

    # Cars
    path("cars/search/", cars_api.car_search, name="api_car_search"),
    path("cars/<int:pk>/", cars_api.car_detail, name="api_car_detail"),

    # Hotels
    path("hotels/search/", hotels_api.hotel_search, name="api_hotel_search"),
    path("hotels/<int:pk>/", hotels_api.hotel_detail, name="api_hotel_detail"),

    # Trips
    path("", include("trips.urls")),
]
