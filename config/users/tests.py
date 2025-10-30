from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

User = get_user_model()


class RegistrationViewTests(TestCase):
    def test_register_get_renders_form(self):
        response = self.client.get(reverse("users:register"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_register_post_creates_user_and_logs_in(self):
        payload = {
            "username": "newtraveler",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        response = self.client.post(reverse("users:register"), payload)
        self.assertRedirects(response, reverse("core:home"))

        user_exists = User.objects.filter(username="newtraveler").exists()
        self.assertTrue(user_exists, "Expected new user to be created")

        session_key = self.client.session.get("_auth_user_id")
        self.assertIsNotNone(session_key, "User should be logged in after registration")


class LoginLogoutViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="traveler", password="StrongPass123!")

    def test_login_authenticates_and_redirects(self):
        response = self.client.post(
            reverse("users:login"),
            {"username": "traveler", "password": "StrongPass123!"},
        )
        self.assertRedirects(response, reverse("core:home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_logout_clears_session(self):
        self.client.login(username="traveler", password="StrongPass123!")
        response = self.client.post(reverse("users:logout"))
        self.assertRedirects(response, reverse("users:login"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_allows_get_request(self):
        self.client.login(username="traveler", password="StrongPass123!")
        response = self.client.get(reverse("users:logout"))
        self.assertRedirects(response, reverse("users:login"))
        self.assertNotIn("_auth_user_id", self.client.session)
