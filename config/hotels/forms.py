from django import forms


class HotelSearchForm(forms.Form):
    """Simple form for natural-language hotel search."""

    query = forms.CharField(
        widget=forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "e.g. I need a 4-star hotel in Paris for 2 guests under $200/night next weekend",
        }),
        label="Describe your hotel needs",
        help_text="Tell us where, when, how many guests, your budget, and any preferences.",
    )
