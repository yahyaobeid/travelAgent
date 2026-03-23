from django import forms


class FlightSearchForm(forms.Form):
    """Simple form for natural-language flight search."""

    query = forms.CharField(
        widget=forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "e.g. Round trip from New York to London, leaving next Friday, returning the following Sunday",
        }),
        label="Describe your flight",
        help_text="Tell us where you're flying, when, and any preferences (cabin class, number of passengers).",
    )
