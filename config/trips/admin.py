from django.contrib import admin
from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ["title", "user", "created_at"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["title", "user__username", "user__email"]
    raw_id_fields = ["itinerary", "flight_search", "car_rental_search"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (None, {
            "fields": ("title", "user")
        }),
        ("Related Items", {
            "fields": ("itinerary", "flight_search", "car_rental_search")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )