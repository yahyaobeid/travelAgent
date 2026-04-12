from django.contrib import admin

from .models import HotelResult, HotelSearch


class HotelResultInline(admin.TabularInline):
    model = HotelResult
    extra = 0
    readonly_fields = ("hotel_name", "hotel_type", "star_rating", "price_display", "location", "listing_url")


@admin.register(HotelSearch)
class HotelSearchAdmin(admin.ModelAdmin):
    list_display = ("location", "check_in_date", "check_out_date", "guests", "star_rating", "user", "created_at")
    list_filter = ("star_rating", "hotel_type")
    search_fields = ("location", "natural_query")
    inlines = [HotelResultInline]


@admin.register(HotelResult)
class HotelResultAdmin(admin.ModelAdmin):
    list_display = ("hotel_name", "hotel_type", "star_rating", "price_display", "location", "source")
    list_filter = ("star_rating", "hotel_type")
    search_fields = ("hotel_name", "location")
