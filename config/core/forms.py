from django import forms

from .models import Itinerary


class ItineraryForm(forms.ModelForm):
    """Form to capture the parameters needed to build an itinerary."""

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
        ]
        widgets = {
            "destination": forms.Textarea(attrs={"rows": 3}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "interests": forms.Textarea(attrs={"rows": 4}),
            "activities": forms.Textarea(attrs={"rows": 4}),
            "food_preferences": forms.Textarea(attrs={"rows": 4}),
            "preference": forms.RadioSelect(),
        }
        labels = {
            "preference": "Travel style",
            "interests": "Trip goals & context",
            "activities": "Activities on your wish list",
            "food_preferences": "Food, drink, and dietary notes",
            "destination": "Where are you staying?",
        }
        help_texts = {
            "destination": (
                "List each city and country in order (include the state code for U.S. stays) "
                "and roughly how long you’ll be in each."
            ),
            "interests": "Share any broader context (travel companions, must-see themes, pacing preferences).",
            "activities": "Tell us about specific tours, experiences, or vibes you’d love to include.",
            "food_preferences": "Let us know cuisines to prioritise, drinks to try, and dietary restrictions or allergies.",
            "preference": "Choose the overall vibe you’d like for this itinerary.",
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "End date must be on or after the start date.")
        return cleaned_data


class ItineraryUpdateForm(ItineraryForm):
    """Form used when editing an itinerary."""

    regenerate_plan = forms.BooleanField(
        required=False,
        initial=False,
        label="Regenerate itinerary with AI",
        help_text="Check to refresh the itinerary using the latest trip details.",
    )

    class Meta(ItineraryForm.Meta):
        fields = [
            "destination",
            "start_date",
            "end_date",
            "interests",
            "activities",
            "food_preferences",
            "preference",
            "generated_plan",
        ]
        widgets = {
            **ItineraryForm.Meta.widgets,
            "generated_plan": forms.Textarea(attrs={"rows": 14}),
        }
