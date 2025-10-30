from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect, render


def register(request):
    """Handle user registration and log the new user in."""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully.")
            return redirect("core:home")
    else:
        form = UserCreationForm()

    return render(request, "users/register.html", {"form": form})


class LogoutViewAllowGet(LogoutView):
    """Allow both GET and POST requests to log out the user."""

    http_method_names = ["get", "post", "head", "options"]

    def get(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
