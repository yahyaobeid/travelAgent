"""
Remove Itinerary, FlightSearch, FlightResult, CarRentalSearch, and CarRentalResult
from core's ORM state. The database tables are retained and owned by their new apps.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_carrentalsearch_carrentalresult"),
        ("itinerary", "0001_initial"),
        ("flights", "0001_initial"),
        ("cars", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name="Itinerary"),
                migrations.DeleteModel(name="FlightSearch"),
                migrations.DeleteModel(name="FlightResult"),
                migrations.DeleteModel(name="CarRentalSearch"),
                migrations.DeleteModel(name="CarRentalResult"),
            ],
            database_operations=[],
        ),
    ]
