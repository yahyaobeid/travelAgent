from django import forms


class CarRentalSearchForm(forms.Form):
    """Simple form for natural-language car rental search."""

    query = forms.CharField(
        widget=forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "e.g. I need an SUV in Miami for under $80/day next weekend",
        }),
        label="Describe your car rental needs",
        help_text="Tell us where, when, what type of car, and your budget.",
    )
