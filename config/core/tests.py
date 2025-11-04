from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from unittest.mock import patch

from .models import Itinerary

User = get_user_model()


class ItineraryEditViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="planner", password="StrongPass123!")
        self.itinerary = Itinerary.objects.create(
            user=self.user,
            destination="Paris",
            start_date="2025-06-01",
            end_date="2025-06-05",
            interests="Museums and food",
            preference=Itinerary.STYLE_GENERAL,
            prompt="Original prompt",
            generated_plan="Day 1: Louvre\nDay 2: Eiffel Tower",
        )

    def test_edit_requires_login(self):
        response = self.client.get(reverse("core:itinerary_edit", args=[self.itinerary.pk]))
        self.assertEqual(response.status_code, 302)

    def test_edit_view_renders_form_for_owner(self):
        self.client.login(username="planner", password="StrongPass123!")
        response = self.client.get(reverse("core:itinerary_edit", args=[self.itinerary.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Update your getaway")
        self.assertContains(response, "Paris")

    def test_edit_updates_without_regeneration(self):
        self.client.login(username="planner", password="StrongPass123!")
        response = self.client.post(
            reverse("core:itinerary_edit", args=[self.itinerary.pk]),
            {
                "destination": "Paris",
                "start_date": "2025-06-02",
                "end_date": "2025-06-06",
                "interests": "Museums, food, and Seine cruise",
                "preference": Itinerary.STYLE_CITY,
                "generated_plan": "Updated plan content",
            },
        )
        self.assertRedirects(response, reverse("core:itinerary_detail", args=[self.itinerary.pk]))
        self.itinerary.refresh_from_db()
        self.assertEqual(self.itinerary.start_date.isoformat(), "2025-06-02")
        self.assertEqual(self.itinerary.generated_plan, "Updated plan content")
        self.assertEqual(self.itinerary.prompt, "Original prompt")
        self.assertEqual(self.itinerary.preference, Itinerary.STYLE_CITY)

    @patch("core.views.generate_itinerary", return_value=("New prompt", "Brand-new plan"))
    def test_edit_regenerates_when_requested(self, mock_generate):
        self.client.login(username="planner", password="StrongPass123!")
        response = self.client.post(
            reverse("core:itinerary_edit", args=[self.itinerary.pk]),
            {
                "destination": "Rome",
                "start_date": "2025-07-01",
                "end_date": "2025-07-05",
                "interests": "History and food",
                "preference": Itinerary.STYLE_CULTURE,
                "generated_plan": "Doesn't matter",
                "regenerate_plan": "on",
            },
        )
        self.assertRedirects(response, reverse("core:itinerary_detail", args=[self.itinerary.pk]))
        self.itinerary.refresh_from_db()
        self.assertEqual(self.itinerary.destination, "Rome")
        self.assertEqual(self.itinerary.prompt, "New prompt")
        self.assertEqual(self.itinerary.generated_plan, "Brand-new plan")
        self.assertEqual(self.itinerary.preference, Itinerary.STYLE_CULTURE)
        mock_generate.assert_called_once()


class ItineraryCreateViewTests(TestCase):
    def setUp(self):
        self.url = reverse("core:itinerary_new")
        self.user = User.objects.create_user(username="creator", password="StrongPass123!")

    def _valid_payload(self, **overrides):
        data = {
            "destination": "Kyoto",
            "start_date": "2025-09-01",
            "end_date": "2025-09-05",
            "interests": "Food",
            "preference": Itinerary.STYLE_GENERAL,
        }
        data.update(overrides)
        return data

    @patch("core.views.generate_itinerary", return_value=("Prompt", "Plan body"))
    def test_preview_available_without_login(self, mock_generate):
        response = self.client.post(
            self.url,
            {**self._valid_payload(), "action": "preview"},
        )
        self.assertRedirects(response, reverse("core:itinerary_preview"))
        response = self.client.get(response.url)
        self.assertContains(response, "Kyoto")
        mock_generate.assert_called_once()

    @patch("core.views.generate_itinerary")
    def test_save_requires_login(self, mock_generate):
        response = self.client.post(
            self.url,
            {**self._valid_payload(), "action": "save"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please sign in to save itineraries to your account.")
        mock_generate.assert_not_called()

    @patch("core.views.generate_itinerary", return_value=("Prompt", "Saved plan"))
    def test_save_persists_for_authenticated_user(self, mock_generate):
        self.client.login(username="creator", password="StrongPass123!")
        response = self.client.post(
            self.url,
            {**self._valid_payload(), "action": "save"},
        )
        itinerary = Itinerary.objects.get(user=self.user)
        self.assertRedirects(response, reverse("core:itinerary_detail", args=[itinerary.pk]))
        self.assertEqual(itinerary.generated_plan, "Saved plan")
        mock_generate.assert_called_once()

    @patch("core.views.generate_itinerary", return_value=("Prompt", "Plan preview"))
    def test_preview_then_save_after_login(self, mock_generate):
        # Preview as anonymous
        self.client.post(self.url, {**self._valid_payload(), "action": "preview"})
        # Login and save pending
        self.client.login(username="creator", password="StrongPass123!")
        response = self.client.post(reverse("core:itinerary_save_pending"))
        itinerary = Itinerary.objects.get(user=self.user)
        self.assertRedirects(response, reverse("core:itinerary_detail", args=[itinerary.pk]))
        self.assertEqual(itinerary.generated_plan, "Plan preview")


class ItineraryDeleteViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="traveler", password="StrongPass123!")
        self.itinerary = Itinerary.objects.create(
            user=self.user,
            destination="Lisbon",
            start_date="2025-08-10",
            end_date="2025-08-15",
            interests="Food and culture",
            preference=Itinerary.STYLE_GENERAL,
            prompt="Prompt",
            generated_plan="Plan",
        )

    def test_delete_requires_login(self):
        response = self.client.get(reverse("core:itinerary_delete", args=[self.itinerary.pk]))
        self.assertEqual(response.status_code, 302)

    def test_delete_confirmation_renders(self):
        self.client.login(username="traveler", password="StrongPass123!")
        response = self.client.get(reverse("core:itinerary_delete", args=[self.itinerary.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Remove this itinerary?")

    def test_delete_post_removes_itinerary(self):
        self.client.login(username="traveler", password="StrongPass123!")
        response = self.client.post(reverse("core:itinerary_delete", args=[self.itinerary.pk]))
        self.assertRedirects(response, reverse("core:home"))
        self.assertFalse(Itinerary.objects.filter(pk=self.itinerary.pk).exists())
