import logging

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

LOGGER = logging.getLogger(__name__)


def _user_data(user) -> dict:
    return {"id": user.pk, "username": user.username}


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")
    if not username or not password:
        return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

    login(request, user)
    LOGGER.info("API login: %s", user.username)
    return Response(_user_data(user))


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    form = UserCreationForm(request.data)
    if not form.is_valid():
        return Response({"errors": form.errors}, status=status.HTTP_400_BAD_REQUEST)

    user = form.save()
    login(request, user)
    LOGGER.info("API register: %s", user.username)
    return Response(_user_data(user), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response(_user_data(request.user))
