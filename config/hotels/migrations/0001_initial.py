from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="HotelSearch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("natural_query", models.TextField()),
                ("location", models.CharField(blank=True, max_length=200)),
                ("check_in_date", models.DateField(blank=True, null=True)),
                ("check_out_date", models.DateField(blank=True, null=True)),
                ("guests", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("max_price_per_night", models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ("star_rating", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("hotel_type", models.CharField(blank=True, max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="hotel_searches",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="HotelResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("hotel_name", models.CharField(max_length=200)),
                ("hotel_type", models.CharField(blank=True, max_length=100)),
                ("star_rating", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("price_per_night", models.DecimalField(decimal_places=2, max_digits=8)),
                ("price_display", models.CharField(max_length=32)),
                ("location", models.CharField(blank=True, max_length=200)),
                ("amenities", models.TextField(blank=True)),
                ("check_in", models.CharField(blank=True, max_length=50)),
                ("check_out", models.CharField(blank=True, max_length=50)),
                ("listing_url", models.URLField(blank=True, max_length=500)),
                ("source", models.CharField(blank=True, max_length=100)),
                ("raw_data", models.JSONField(default=dict)),
                ("fetched_at", models.DateTimeField(auto_now_add=True)),
                (
                    "search",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="results",
                        to="hotels.hotelsearch",
                    ),
                ),
            ],
            options={"ordering": ["price_per_night"]},
        ),
    ]
