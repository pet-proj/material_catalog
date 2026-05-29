from django.contrib import admin
from .models import Category, Tag, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "sku", "category", "unit_of_measure"]
    list_filter = ["category", "tags"]
    search_fields = ["name", "sku", "description"]
    filter_horizontal = ["tags"]
