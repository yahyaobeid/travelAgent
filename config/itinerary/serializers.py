from datetime import date

from rest_framework import serializers

from .models import Itinerary


class ItinerarySerializer(serializers.ModelSerializer):
    style_label = serializers.SerializerMethodField()

    class Meta:
        model = Itinerary
        fields = [
            "id",
            "destination",
            "start_date",
            "end_date",
            "interests",
            "activities",
            "food_preferences",
            "preference",
            "style_label",
            "generated_plan",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "style_label"]

    def get_style_label(self, obj) -> str:
        return dict(Itinerary.STYLE_CHOICES).get(obj.preference, obj.preference)


class ItineraryCreateSerializer(serializers.Serializer):
    destination = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    interests = serializers.CharField(allow_blank=True, default="")
    activities = serializers.CharField(allow_blank=True, default="")
    food_preferences = serializers.CharField(allow_blank=True, default="")
    preference = serializers.ChoiceField(
        choices=Itinerary.STYLE_CHOICES,
        default=Itinerary.STYLE_GENERAL,
    )
    action = serializers.ChoiceField(choices=["preview", "save"], default="preview")

    def validate(self, data):
        if data["end_date"] < data["start_date"]:
            raise serializers.ValidationError({"end_date": "End date must be on or after the start date."})
        return data


class ItineraryUpdateSerializer(serializers.ModelSerializer):
    regenerate_plan = serializers.BooleanField(required=False, default=False, write_only=True)

    class Meta:
        model = Itinerary
        fields = [
            "destination",
            "start_date",
            "end_date",
            "interests",
            "activities",
            "food_preferences",
            "preference",
            "generated_plan",
            "regenerate_plan",
        ]

    def validate(self, data):
        start = data.get("start_date", self.instance.start_date if self.instance else None)
        end = data.get("end_date", self.instance.end_date if self.instance else None)
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "End date must be on or after the start date."})
        return data
