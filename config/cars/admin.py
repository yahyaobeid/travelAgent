from django.contrib import admin

from .models import CarRentalResult, CarRentalSearch


@admin.register(CarRentalSearch)
class CarRentalSearchAdmin(admin.ModelAdmin):
    list_display = ("location", "car_type", "pickup_date", "dropoff_date", "user", "created_at")
    list_filter = ("pickup_date", "dropoff_date", "created_at")
    search_fields = ("location", "car_type", "user__username")


@admin.register(CarRentalResult)
class CarRentalResultAdmin(admin.ModelAdmin):
    list_display = ("car_name", "car_type", "price_per_day", "rental_company", "location", "search")
    list_filter = ("car_type", "rental_company")
    search_fields = ("car_name", "rental_company", "location")
