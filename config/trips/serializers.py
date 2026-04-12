from rest_framework import serializers
from .models import Trip
from itinerary.models import Itinerary
from flights.models import FlightSearch
from cars.models import CarRentalSearch


class ItineraryNestedSerializer(serializers.ModelSerializer):
    """Read-only nested serializer for Itinerary"""
    class Meta:
        model = Itinerary
        fields = ["id", "destination", "start_date", "end_date", "preference", "generated_plan"]
        read_only_fields = ["id", "destination", "start_date", "end_date", "preference", "generated_plan"]


class FlightSearchNestedSerializer(serializers.ModelSerializer):
    """Read-only nested serializer for FlightSearch"""
    class Meta:
        model = FlightSearch
        fields = ["id", "natural_query"]
        read_only_fields = ["id", "natural_query"]


class CarRentalSearchNestedSerializer(serializers.ModelSerializer):
    """Read-only nested serializer for CarRentalSearch"""
    class Meta:
        model = CarRentalSearch
        fields = ["id", "natural_query", "location"]
        read_only_fields = ["id", "natural_query", "location"]


class TripSerializer(serializers.ModelSerializer):
    """Full Trip serializer with nested related objects"""
    itinerary = ItineraryNestedSerializer(read_only=True)
    flight_search = FlightSearchNestedSerializer(read_only=True)
    car_rental_search = CarRentalSearchNestedSerializer(read_only=True)

    # Write-only fields for setting foreign key relationships
    itinerary_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    flight_search_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    car_rental_search_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Trip
        fields = [
            "id",
            "title",
            "user",
            "itinerary",
            "flight_search",
            "car_rental_search",
            "itinerary_id",
            "flight_search_id",
            "car_rental_search_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

    def create(self, validated_data):
        # Extract foreign key IDs
        itinerary_id = validated_data.pop('itinerary_id', None)
        flight_search_id = validated_data.pop('flight_search_id', None)
        car_rental_search_id = validated_data.pop('car_rental_search_id', None)

        trip = Trip.objects.create(**validated_data)

        # Set foreign key relationships if provided
        if itinerary_id:
            trip.itinerary_id = itinerary_id
        if flight_search_id:
            trip.flight_search_id = flight_search_id
        if car_rental_search_id:
            trip.car_rental_search_id = car_rental_search_id

        trip.save()
        return trip

    def update(self, instance, validated_data):
        # Extract foreign key IDs
        itinerary_id = validated_data.pop('itinerary_id', None)
        flight_search_id = validated_data.pop('flight_search_id', None)
        car_rental_search_id = validated_data.pop('car_rental_search_id', None)

        # Update regular fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Update foreign key relationships if provided
        if 'itinerary_id' in self.initial_data:
            instance.itinerary_id = itinerary_id
        if 'flight_search_id' in self.initial_data:
            instance.flight_search_id = flight_search_id
        if 'car_rental_search_id' in self.initial_data:
            instance.car_rental_search_id = car_rental_search_id

        instance.save()
        return instance