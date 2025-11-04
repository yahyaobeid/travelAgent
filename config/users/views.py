from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme


def register(request):
    """Handle user registration and log the new user in."""
    next_url = request.POST.get("next") or request.GET.get("next")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully.")
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect("core:home")
    else:
        form = UserCreationForm()

    return render(request, "users/register.html", {"form": form, "next": next_url})


class LogoutViewAllowGet(LogoutView):
    """Allow both GET and POST requests to log out the user."""

    http_method_names = ["get", "post", "head", "options"]

    def get(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
