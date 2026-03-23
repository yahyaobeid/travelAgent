from django.urls import path

from . import views

app_name = "flights"

urlpatterns = [
    path("", views.search, name="search"),
    path("results/", views.results, name="results"),
    path("<int:pk>/", views.detail, name="detail"),
]
