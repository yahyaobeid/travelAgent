from rest_framework import serializers


class CarRentalQuerySerializer(serializers.Serializer):
    query = serializers.CharField()


class CarRentalListingSerializer(serializers.Serializer):
    car_name = serializers.CharField()
    car_type = serializers.CharField()
    price_per_day = serializers.FloatField()
    price_display = serializers.CharField()
    rental_company = serializers.CharField()
    location = serializers.CharField()
    availability = serializers.CharField(allow_blank=True)
    listing_url = serializers.CharField(allow_blank=True)
    source = serializers.CharField(allow_blank=True)
