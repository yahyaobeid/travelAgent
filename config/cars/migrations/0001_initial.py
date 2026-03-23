"""
Move CarRentalSearch and CarRentalResult model states from core to cars app.
The database tables (core_carrentalsearch, core_carrentalresult) already exist — only ORM state moves.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0006_carrentalsearch_carrentalresult"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="CarRentalSearch",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("natural_query", models.TextField()),
                        ("location", models.CharField(blank=True, max_length=200)),
                        ("car_type", models.CharField(blank=True, max_length=50)),
                        ("max_price_per_day", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                        ("pickup_date", models.DateField(blank=True, null=True)),
                        ("dropoff_date", models.DateField(blank=True, null=True)),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("user", models.ForeignKey(
                            blank=True,
                            null=True,
                            on_delete=django.db.models.deletion.CASCADE,
                            related_name="car_rental_searches",
                            to=settings.AUTH_USER_MODEL,
                        )),
                    ],
                    options={
                        "ordering": ["-created_at"],
                        "db_table": "core_carrentalsearch",
                    },
                ),
                migrations.CreateModel(
                    name="CarRentalResult",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("car_name", models.CharField(max_length=200)),
                        ("car_type", models.CharField(max_length=50)),
                        ("price_per_day", models.DecimalField(decimal_places=2, max_digits=8)),
                        ("price_display", models.CharField(max_length=32)),
                        ("rental_company", models.CharField(max_length=100)),
                        ("location", models.CharField(max_length=200)),
                        ("availability", models.CharField(blank=True, max_length=100)),
                        ("listing_url", models.URLField(blank=True, max_length=500)),
                        ("source", models.CharField(blank=True, max_length=100)),
                        ("raw_data", models.JSONField(default=dict)),
                        ("fetched_at", models.DateTimeField(auto_now_add=True)),
                        ("search", models.ForeignKey(
                            on_delete=django.db.models.deletion.CASCADE,
                            related_name="results",
                            to="cars.carrentalsearch",
                        )),
                    ],
                    options={
                        "ordering": ["price_per_day"],
                        "db_table": "core_carrentalresult",
                    },
                ),
            ],
            database_operations=[],
        ),
    ]
