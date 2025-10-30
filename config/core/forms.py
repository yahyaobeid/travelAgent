from django import forms

from .models import Itinerary


class ItineraryForm(forms.ModelForm):
    """Form to capture the parameters needed to build an itinerary."""

    class Meta:
        model = Itinerary
        fields = ["destination", "start_date", "end_date", "interests"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "interests": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_date")
        end = cleaned_data.get("end_date")
        if start and end and end < start:
            self.add_error("end_date", "End date must be on or after the start date.")
        return cleaned_data
