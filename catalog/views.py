from django.shortcuts import render, redirect
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Product, Category, Tag


def product_list(request):
    categories = Category.objects.all().order_by("name")
    tags = Tag.objects.all().order_by("name")

    # ── Base Queryset ─────────────────────────────────────────────────────
    # select_related('category') performs a SQL JOIN upfront so that
    # accessing product.category.name in the template does NOT fire
    # an additional query per row (avoids the N+1 query problem).
    #
    # prefetch_related('tags') handles the ManyToMany side — Django
    # fetches all relevant tags in a second query and maps them in
    # Python, which is more efficient than a JOIN for M2M relationships.
    #
    # Without these two, a table of 20 products would fire:
    #   1 (products) + 20 (categories) + 20 (tags) = 41 queries
    # With them: exactly 3 queries regardless of result size.
    products = (
        Product.objects.select_related("category")
        .prefetch_related("tags")
        .order_by("name")
    )

    # ── Read Filter Parameters from GET Request ───────────────────────────
    query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "")

    # getlist() handles multiple checkbox values from the same field name
    # e.g. ?tags=1&tags=3&tags=5 → ['1', '3', '5']
    selected_tags = request.GET.getlist("tags")

    # ── Apply Filters Conditionally ───────────────────────────────────────
    # Filters are chained only when the user provides a value.
    # Each .filter() call refines the queryset without hitting the DB.
    # Django is lazy — it waits until the template iterates the results
    # before executing the final compiled SQL query.

    if query:
        # Q objects allow OR logic across multiple fields in one query.
        # This is equivalent to:
        # WHERE (name LIKE '%wire%' OR description LIKE '%wire%')
        #
        # icontains = case-insensitive LIKE — works across all databases.
        #
        # Future: replace with SearchVector + SearchQuery for PostgreSQL
        # to enable ranked full-text search with index support:
        # from django.contrib.postgres.search import SearchVector, SearchQuery
        # products = products.annotate(search=SearchVector('name','description'))
        #                    .filter(search=SearchQuery(query))
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if selected_category:
        # Simple equality filter on the ForeignKey.
        # SQL: WHERE category_id = <selected_category>
        #
        # Future: if filtering by category tree (parent/child categories),
        # use django-mptt or django-treebeard for hierarchical queries.
        products = products.filter(category_id=selected_category)

    if selected_tags:
        # Filter across ManyToMany relationship.
        # SQL: INNER JOIN ... WHERE tag.id IN (1, 3, 5)
        #
        # .distinct() is required here — without it, a product with
        # 3 matching tags would appear 3 times in results due to
        # how SQL JOIN works with junction tables.
        #
        # Current behavior: OR logic — returns products matching ANY
        # of the selected tags.
        #
        # Future: to implement AND logic (match ALL selected tags),
        # chain individual filter() calls instead:
        #   for tag_id in selected_tags:
        #       products = products.filter(tags__id=tag_id)
        # This generates a separate JOIN per tag, guaranteeing all match.
        products = products.filter(tags__id__in=selected_tags).distinct()

    paginator = Paginator(products, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    favourite_ids = request.session.get("favourites", [])

    # ── Context ───────────────────────────────────────────────────────────
    # At this point, no SQL has been executed yet.
    # The queryset is evaluated (SQL fires) when the template
    # iterates over 'products' with {% for product in products %}.
    context = {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": categories,
        "tags": tags,
        "query": query,
        "selected_category": selected_category,
        "selected_tags": selected_tags,
        "favourite_ids": favourite_ids,
    }

    return render(request, "catalog/product_list.html", context)


def toggle_favourite(request, product_id):
    """
    Adds or removes a product from the user's favourites list.

    Favourites are stored in the Django session as a list of product IDs.
    No authentication or database model is required — the session persists
    across page loads for the same browser automatically.

    Session structure:
        request.session['favourites'] = [1, 5, 12, 17]

    Toggle logic:
        - If product_id is in the list → remove it (unfavourite)
        - If product_id is not in the list → add it (favourite)

    session.modified = True is required when mutating a mutable object
    (like a list) inside the session. Without it Django does not detect
    the change and will not save the updated session to the database.

    Future consideration:
        If user authentication is introduced, favourites should be
        migrated to a database model:
        Favourite(user=ForeignKey, product=ForeignKey)
        This would allow favourites to persist across devices and browsers.
    """
    favourites = request.session.get("favourites", [])

    if product_id in favourites:
        favourites.remove(product_id)
    else:
        favourites.append(product_id)

    request.session["favourites"] = favourites
    request.session.modified = True

    # Preserve current filter state when redirecting back
    # so the user lands on the same filtered page they were on
    redirect_url = request.META.get("HTTP_REFERER", "/")
    return redirect(redirect_url)


def favourites_list(request):
    """
    Displays only the products the user has favourited.

    Reads the favourites list from the session and filters
    the product queryset to only return those product IDs.

    SQL: WHERE product.id IN (1, 5, 12, 17)

    select_related and prefetch_related are applied for the
    same N+1 reasons as the main product list view.

    If the session has no favourites, an empty queryset is returned
    rather than all products — fail safe by default.
    """
    favourite_ids = request.session.get("favourites", [])

    products = (
        Product.objects.filter(id__in=favourite_ids)
        .select_related("category")
        .prefetch_related("tags")
        .order_by("name")
    )

    categories = Category.objects.all().order_by("name")
    tags = Tag.objects.all().order_by("name")

    context = {
        "products": products,
        "categories": categories,
        "tags": tags,
        "favourite_ids": favourite_ids,
        "total_count": products.count(),
        "is_favourites_page": True,
    }

    return render(request, "catalog/favourites.html", context)
