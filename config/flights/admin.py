from django.contrib import admin

from .models import FlightResult, FlightSearch


@admin.register(FlightSearch)
class FlightSearchAdmin(admin.ModelAdmin):
    list_display = ("origin_airport", "destination_airport", "departure_date", "user", "created_at")
    list_filter = ("departure_date", "cabin_class", "created_at")
    search_fields = ("origin_airport", "destination_airport", "user__username")


@admin.register(FlightResult)
class FlightResultAdmin(admin.ModelAdmin):
    list_display = ("airline", "flight_number", "departure_time", "arrival_time", "price_cents", "search")
    list_filter = ("airline", "stops")
    search_fields = ("airline", "flight_number")
