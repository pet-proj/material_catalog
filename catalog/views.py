from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Product, Category, Tag, SavedFilter


def product_list(request):

    # ── Sidebar Data ──────────────────────────────────────────────────────
    categories = Category.objects.all().order_by("name")
    tags = Tag.objects.all().order_by("name")
    saved_filters = (
        SavedFilter.objects.prefetch_related("tags").select_related("category").all()
    )

    # ── Base Queryset ─────────────────────────────────────────────────────
    # select_related and prefetch_related solve the N+1 query problem.
    # Without these, a page of 10 products fires 21 queries.
    # With these, it always fires exactly 3 queries regardless of page size.
    products = (
        Product.objects.select_related("category")
        .prefetch_related("tags")
        .order_by("name")
    )

    # ── Read Filter Parameters ────────────────────────────────────────────
    query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "")
    selected_tags = request.GET.getlist("tags")

    # ── Apply Filters Conditionally ───────────────────────────────────────
    if query:
        # Q objects allow OR logic across multiple fields in one query.
        # SQL: WHERE (name LIKE '%wire%' OR description LIKE '%wire%')
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if selected_category:
        # SQL: WHERE category_id = <selected_category>
        products = products.filter(category_id=selected_category)

    if selected_tags:
        # SQL: INNER JOIN ... WHERE tag.id IN (1, 3, 5)
        # .distinct() prevents duplicate rows from ManyToMany JOIN.
        products = products.filter(tags__id__in=selected_tags).distinct()

    # ── Pagination ────────────────────────────────────────────────────────
    # Adds LIMIT 10 OFFSET n to the final SQL query.
    # Only 10 rows fetched from DB per request regardless of dataset size.
    paginator = Paginator(products, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": categories,
        "tags": tags,
        "saved_filters": saved_filters,
        "query": query,
        "selected_category": selected_category,
        "selected_tags": selected_tags,
        "total_count": paginator.count,
    }

    return render(request, "catalog/product_list.html", context)


def save_filter(request):
    """
    Saves the current search and filter state as a named SavedFilter.

    Accepts POST only. Reads filter parameters from the form,
    creates a SavedFilter instance, and attaches the selected tags
    via the ManyToMany relationship.

    Redirects back to the product list after saving so the user
    sees their saved filter appear immediately in the sidebar.
    """
    if request.method == "POST":
        name = request.POST.get("filter_name", "").strip()

        # Only save if the user provided a name
        if name:
            saved = SavedFilter.objects.create(
                name=name,
                query=request.POST.get("q", ""),
                category_id=request.POST.get("category") or None,
            )

            # Attach selected tags via ManyToMany
            # .set() replaces all existing tags in one efficient query
            tag_ids = request.POST.getlist("tags")
            if tag_ids:
                saved.tags.set(tag_ids)

    return redirect("catalog:product_list")


def delete_filter(request, filter_id):
    """
    Deletes a saved filter by id.

    Accepts POST only to prevent accidental deletion via GET requests
        e.g. a browser prefetching links.

    get_object_or_404 returns a clean 404 response if the filter
    does not exist rather than raising an unhandled exception.
    """
    if request.method == "POST":
        saved_filter = get_object_or_404(SavedFilter, id=filter_id)
        saved_filter.delete()

    return redirect("catalog:product_list")
