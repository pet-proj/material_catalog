from django.conf import settings
from django.shortcuts import render, redirect
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Product, Category, Tag, Favourite


def _get_favourite_ids(request):
    if request.user.is_authenticated:
        return list(
            Favourite.objects.filter(user=request.user).values_list('product_id', flat=True)
        )
    return []


def product_list(request):
    categories = Category.objects.all().order_by("name")
    tags = Tag.objects.all().order_by("name")

    products = (
        Product.objects.select_related("category")
        .prefetch_related("tags")
        .order_by("name")
    )

    query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "")
    selected_tags = request.GET.getlist("tags")

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if selected_category:
        products = products.filter(category_id=selected_category)

    if selected_tags:
        products = products.filter(tags__id__in=selected_tags).distinct()

    paginator = Paginator(products, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": categories,
        "tags": tags,
        "query": query,
        "selected_category": selected_category,
        "selected_tags": selected_tags,
        "favourite_ids": _get_favourite_ids(request),
    }

    return render(request, "catalog/product_list.html", context)


def toggle_favourite(request, product_id):
    if not request.user.is_authenticated:
        return redirect(f"{settings.LOGIN_URL}?next={request.META.get('HTTP_REFERER', '/')}")

    favourite, created = Favourite.objects.get_or_create(user=request.user, product_id=product_id)
    if not created:
        favourite.delete()

    return redirect(request.META.get("HTTP_REFERER", "/"))


def favourites_list(request):
    if not request.user.is_authenticated:
        return redirect(f"{settings.LOGIN_URL}?next=/favourites/")

    favourite_ids = list(
        Favourite.objects.filter(user=request.user).values_list('product_id', flat=True)
    )

    products = (
        Product.objects.filter(id__in=favourite_ids)
        .select_related("category")
        .prefetch_related("tags")
        .order_by("name")
    )

    context = {
        "products": products,
        "favourite_ids": favourite_ids,
        "total_count": products.count(),
        "is_favourites_page": True,
    }

    return render(request, "catalog/favourites.html", context)
