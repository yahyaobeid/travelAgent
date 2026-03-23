"""
Move FlightSearch and FlightResult model states from core to flights app.
The database tables (core_flightsearch, core_flightresult) already exist — only ORM state moves.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0005_flightsearch_flightresult"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="FlightSearch",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("natural_query", models.TextField()),
                        ("origin_airport", models.CharField(max_length=10)),
                        ("destination_airport", models.CharField(max_length=10)),
                        ("departure_date", models.DateField()),
                        ("return_date", models.DateField(blank=True, null=True)),
                        ("passengers", models.PositiveSmallIntegerField(default=1)),
                        ("cabin_class", models.CharField(default="economy", max_length=16)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("user", models.ForeignKey(
                            blank=True,
                            null=True,
                            on_delete=django.db.models.deletion.CASCADE,
                            related_name="flight_searches",
                            to=settings.AUTH_USER_MODEL,
                        )),
                    ],
                    options={
                        "ordering": ["-created_at"],
                        "db_table": "core_flightsearch",
                    },
                ),
                migrations.CreateModel(
                    name="FlightResult",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("airline", models.CharField(max_length=100)),
                        ("flight_number", models.CharField(blank=True, max_length=32)),
                        ("departure_time", models.CharField(max_length=32)),
                        ("arrival_time", models.CharField(max_length=32)),
                        ("duration", models.CharField(max_length=32)),
                        ("stops", models.PositiveSmallIntegerField(default=0)),
                        ("price_cents", models.PositiveIntegerField()),
                        ("currency", models.CharField(default="USD", max_length=3)),
                        ("booking_url", models.URLField(blank=True)),
                        ("raw_data", models.JSONField(default=dict)),
                        ("fetched_at", models.DateTimeField(auto_now_add=True)),
                        ("search", models.ForeignKey(
                            on_delete=django.db.models.deletion.CASCADE,
                            related_name="results",
                            to="flights.flightsearch",
                        )),
                    ],
                    options={
                        "ordering": ["price_cents"],
                        "db_table": "core_flightresult",
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
