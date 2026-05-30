from django.shortcuts import render
from .models import Product, Category, Tag


def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    tags = Tag.objects.all()

    query = request.GET.get("q", "")
    selected_category = request.GET.get("category", "")
    selected_tags = request.GET.getlist("tags")

    if query:
        products = products.filter(description__icontains=query) | products.filter(
            name__icontains=query
        )

    if selected_category:
        products = products.filter(category_id=selected_category)

    if selected_tags:
        products = products.filter(tags__in=selected_tags).distinct()

    context = {
        "products": products,
        "categories": categories,
        "tags": tags,
        "query": query,
        "selected_category": selected_category,
        "selected_tags": selected_tags,
    }

    return render(request, "catalog/product_list.html", context)
