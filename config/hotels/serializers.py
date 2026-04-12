from rest_framework import serializers


class HotelQuerySerializer(serializers.Serializer):
    query = serializers.CharField()


class HotelListingSerializer(serializers.Serializer):
    hotel_name = serializers.CharField()
    hotel_type = serializers.CharField(allow_blank=True)
    star_rating = serializers.IntegerField(allow_null=True)
    price_per_night = serializers.FloatField()
    price_display = serializers.CharField()
    location = serializers.CharField(allow_blank=True)
    amenities = serializers.CharField(allow_blank=True)
    check_in = serializers.CharField(allow_blank=True)
    check_out = serializers.CharField(allow_blank=True)
    listing_url = serializers.CharField(allow_blank=True)
    source = serializers.CharField(allow_blank=True)
