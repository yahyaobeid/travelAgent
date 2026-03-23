"""
Move Itinerary model state from core to itinerary app.
The database table (core_itinerary) already exists — only the ORM state moves.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0004_alter_itinerary_destination"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="Itinerary",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("destination", models.TextField()),
                        ("start_date", models.DateField()),
                        ("end_date", models.DateField()),
                        ("interests", models.TextField(blank=True)),
                        ("activities", models.TextField(blank=True, help_text="Specific activities or experiences the traveler wants to prioritise.")),
                        ("food_preferences", models.TextField(blank=True, help_text="Cuisine preferences, must-try drinks, and any dietary restrictions to keep in mind.")),
                        ("preference", models.CharField(
                            choices=[
                                ("general", "No preference / Balanced"),
                                ("culture_history", "Culture & History"),
                                ("city_shopping", "City Life & Shopping"),
                                ("adventure", "Adventure & Outdoors"),
                            ],
                            default="general",
                            help_text="Overall tone for the generated itinerary.",
                            max_length=32,
                        )),
                        ("prompt", models.TextField()),
                        ("generated_plan", models.TextField()),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("user", models.ForeignKey(
                            on_delete=django.db.models.deletion.CASCADE,
                            related_name="itineraries",
                            to=settings.AUTH_USER_MODEL,
                        )),
                    ],
                    options={
                        "ordering": ["-created_at"],
                        "db_table": "core_itinerary",
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
