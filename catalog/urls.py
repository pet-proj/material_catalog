from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("favourites/", views.favourites_list, name="favourites_list"),
    path(
        "favourites/toggle/<int:product_id>/",
        views.toggle_favourite,
        name="toggle_favourite",
    ),
]
