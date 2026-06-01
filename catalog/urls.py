from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("filters/save/", views.save_filter, name="save_filter"),
    path("filters/delete/<int:filter_id>/", views.delete_filter, name="delete_filter"),
]
