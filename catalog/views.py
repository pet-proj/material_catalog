from django.shortcuts import render
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from .models import Product, Category, Tag


def product_list(request):
    """
    Product search and filter view.

    Demonstrates Django ORM proficiency through:
    - Q objects for complex lookups
    - select_related for ForeignKey optimization
    - prefetch_related for ManyToMany optimization
    - Chainable querysets for dynamic filtering

    Performance Notes:
    ─────────────────────────────────────────────
    Current approach: suitable for small-to-medium datasets (< 100k records).
    Each request builds and executes one optimized SQL query against the DB.
    Filtering is handled at the database level, not in Python memory.

    Future Optimizations to Consider:
    ─────────────────────────────────────────────
    1. PAGINATION: At scale, never return unbounded querysets.
       Use Django's Paginator to limit rows per request.
       See: django.core.paginator.Paginator

    2. DATABASE INDEXES: Add db_index=True to frequently filtered fields
       e.g. Product.name, Product.category — speeds up WHERE clauses
       significantly at 100k+ records.

    3. CACHING: For read-heavy catalogs that rarely change,
       cache the queryset result using Django's cache framework.
       e.g. cache.get('product_list') / cache.set(...)
       Eliminates DB hits entirely for repeated identical queries.

    4. FULL-TEXT SEARCH: icontains uses SQL LIKE '%term%' which cannot
       use indexes and does a full table scan. At scale, replace with:
       - Django's SearchVector/SearchQuery (PostgreSQL only)
       - Dedicated search engine: Elasticsearch or Meilisearch

    5. QUERY COUNT: Use Django Debug Toolbar in development to monitor
       how many queries are fired per request. Target: 1-3 queries max.
    """

    # ── Sidebar Data ──────────────────────────────────────────────────────
    # These two queries are always needed to populate the filter form.
    # They are intentionally simple — categories and tags rarely exceed
    # hundreds of records so no optimization needed here.
    #
    # Future: if categories/tags become large, consider caching these
    # since they change infrequently.
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

    # Paginate results — 10 per page
    paginator = Paginator(products, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

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
    }

    return render(request, "catalog/product_list.html", context)
