from django.contrib import admin

from .models import Itinerary


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ("destination", "user", "start_date", "end_date", "created_at")
    list_filter = ("start_date", "end_date", "created_at")
    search_fields = ("destination", "user__username", "user__email")
