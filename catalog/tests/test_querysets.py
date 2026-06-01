from django.db.models import Q
from django.test import TestCase

from catalog.models import Category, Product, Tag


def _apply_filters(query="", category_id="", tag_ids=None):
    """Mirror the filtering logic in product_list view for direct ORM testing."""
    qs = (
        Product.objects.select_related("category")
        .prefetch_related("tags")
        .order_by("name")
    )
    if query:
        qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_id:
        qs = qs.filter(category_id=category_id)
    if tag_ids:
        qs = qs.filter(tags__id__in=tag_ids).distinct()
    return qs


class ProductFilterTests(TestCase):
    """Tests for the ORM filtering logic used by the product_list view."""

    @classmethod
    def setUpTestData(cls):
        # Clear seed migration data so tests own their fixtures entirely.
        # setUpTestData runs inside a savepoint that is rolled back after the
        # class, so seed data is restored for unrelated test classes.
        Product.objects.all().delete()
        Category.objects.all().delete()
        Tag.objects.all().delete()

        cls.cat_elec = Category.objects.create(name="Electrical")
        cls.cat_tools = Category.objects.create(name="Tools")

        cls.tag_stock = Tag.objects.create(name="in-stock")
        cls.tag_outdoor = Tag.objects.create(name="outdoor-rated")
        cls.tag_bulk = Tag.objects.create(name="bulk-discount")

        # "power" appears in p_drill's NAME and p_conduit's DESCRIPTION,
        # which exercises the OR logic across both fields in one query.
        cls.p_wire = Product.objects.create(
            name="Copper Wire", sku="W-001",
            description="flexible conductor", category=cls.cat_elec,
        )
        cls.p_wire.tags.set([cls.tag_stock, cls.tag_outdoor])

        cls.p_breaker = Product.objects.create(
            name="Circuit Breaker", sku="B-001",
            description="20A protection device", category=cls.cat_elec,
        )
        cls.p_breaker.tags.set([cls.tag_stock])

        cls.p_drill = Product.objects.create(
            name="Power Drill", sku="D-001",
            description="heavy duty tool", category=cls.cat_tools,
        )
        cls.p_drill.tags.set([cls.tag_bulk])

        cls.p_conduit = Product.objects.create(
            name="EMT Conduit", sku="C-001",
            description="power-rated conduit", category=cls.cat_tools,
        )
        cls.p_conduit.tags.set([cls.tag_outdoor, cls.tag_bulk])

    # -- Text Search --

    def test_search_matches_name(self):
        pks = set(_apply_filters(query="wire").values_list("pk", flat=True))
        self.assertEqual(pks, {self.p_wire.pk})

    def test_search_matches_description(self):
        pks = set(_apply_filters(query="protection").values_list("pk", flat=True))
        self.assertEqual(pks, {self.p_breaker.pk})

    def test_search_is_case_insensitive(self):
        pks = set(_apply_filters(query="COPPER").values_list("pk", flat=True))
        self.assertEqual(pks, {self.p_wire.pk})

    def test_search_empty_string_returns_all(self):
        self.assertEqual(_apply_filters(query="").count(), 4)

    def test_search_no_match_returns_empty(self):
        self.assertEqual(_apply_filters(query="xyznotfound").count(), 0)

    def test_search_or_logic_matches_name_and_description(self):
        # "power" → p_drill by NAME, p_conduit by DESCRIPTION
        pks = set(_apply_filters(query="power").values_list("pk", flat=True))
        self.assertEqual(pks, {self.p_drill.pk, self.p_conduit.pk})

    # -- Category Filter --

    def test_category_filter_returns_matching_products(self):
        pks = set(_apply_filters(category_id=self.cat_elec.id).values_list("pk", flat=True))
        self.assertEqual(pks, {self.p_wire.pk, self.p_breaker.pk})

    def test_category_filter_excludes_other_categories(self):
        pks = set(_apply_filters(category_id=self.cat_tools.id).values_list("pk", flat=True))
        self.assertEqual(pks, {self.p_drill.pk, self.p_conduit.pk})

    def test_empty_category_id_skips_filter(self):
        self.assertEqual(_apply_filters(category_id="").count(), 4)

    # -- Tag Filter --

    def test_tag_filter_single_tag(self):
        pks = set(_apply_filters(tag_ids=[self.tag_stock.id]).values_list("pk", flat=True))
        self.assertEqual(pks, {self.p_wire.pk, self.p_breaker.pk})

    def test_tag_filter_multiple_tags_uses_or_logic(self):
        # tag_stock → wire, breaker; tag_bulk → drill, conduit → all 4
        pks = set(
            _apply_filters(tag_ids=[self.tag_stock.id, self.tag_bulk.id])
            .values_list("pk", flat=True)
        )
        self.assertEqual(pks, {self.p_wire.pk, self.p_breaker.pk, self.p_drill.pk, self.p_conduit.pk})

    def test_tag_filter_distinct_prevents_duplicates(self):
        # p_conduit has both tag_outdoor AND tag_bulk; filtering by both must not duplicate it
        qs = _apply_filters(tag_ids=[self.tag_outdoor.id, self.tag_bulk.id])
        pks = list(qs.values_list("pk", flat=True))
        self.assertEqual(pks.count(self.p_conduit.pk), 1)

    def test_none_tag_list_skips_filter(self):
        self.assertEqual(_apply_filters(tag_ids=None).count(), 4)

    # -- Combined Filters --

    def test_search_plus_category(self):
        pks = set(
            _apply_filters(query="wire", category_id=self.cat_elec.id)
            .values_list("pk", flat=True)
        )
        self.assertEqual(pks, {self.p_wire.pk})

    def test_category_plus_tags(self):
        pks = set(
            _apply_filters(category_id=self.cat_tools.id, tag_ids=[self.tag_outdoor.id])
            .values_list("pk", flat=True)
        )
        self.assertEqual(pks, {self.p_conduit.pk})

    def test_all_three_filters(self):
        pks = set(
            _apply_filters(
                query="conduit",
                category_id=self.cat_tools.id,
                tag_ids=[self.tag_outdoor.id],
            ).values_list("pk", flat=True)
        )
        self.assertEqual(pks, {self.p_conduit.pk})

    def test_conflicting_filters_return_empty(self):
        # "wire" only exists in cat_elec; filtering by cat_tools → no match
        self.assertEqual(
            _apply_filters(query="wire", category_id=self.cat_tools.id).count(), 0
        )


class ProductQueryCountTests(TestCase):
    """Verify select_related / prefetch_related prevent N+1 queries."""

    @classmethod
    def setUpTestData(cls):
        Product.objects.all().delete()
        Category.objects.all().delete()
        Tag.objects.all().delete()

        categories = [Category.objects.create(name=f"Cat {i}") for i in range(3)]
        tags = [Tag.objects.create(name=f"Tag {i}") for i in range(5)]
        cls.a_category = categories[0]
        cls.a_tag = tags[0]
        cls.products = []
        for i in range(15):
            p = Product.objects.create(
                name=f"Product {i:02d}",
                sku=f"SKU-{i:03d}",
                description="test item",
                category=categories[i % 3],
            )
            p.tags.add(tags[i % 5])
            cls.products.append(p)

    def test_select_related_prevents_category_n_plus_one(self):
        # Without select_related this would be 1 + 15 queries; with it: 1.
        qs = Product.objects.select_related("category").order_by("name")
        with self.assertNumQueries(1):
            _ = [p.category.name for p in list(qs)]

    def test_prefetch_related_prevents_tags_n_plus_one(self):
        # Without prefetch_related this would be 1 + 15 queries; with it: 2.
        qs = Product.objects.prefetch_related("tags").order_by("name")
        with self.assertNumQueries(2):
            _ = [list(p.tags.all()) for p in list(qs)]

    def test_combined_optimisation_uses_two_queries(self):
        qs = (
            Product.objects.select_related("category")
            .prefetch_related("tags")
            .order_by("name")
        )
        with self.assertNumQueries(2):
            products = list(qs)
            _ = [(p.category.name, list(p.tags.all())) for p in products]

    def test_category_filter_does_not_add_queries(self):
        qs = (
            Product.objects.select_related("category")
            .prefetch_related("tags")
            .filter(category_id=self.a_category.id)
            .order_by("name")
        )
        with self.assertNumQueries(2):
            products = list(qs)
            _ = [(p.category.name, list(p.tags.all())) for p in products]

    def test_tag_filter_does_not_add_queries(self):
        qs = (
            Product.objects.select_related("category")
            .prefetch_related("tags")
            .filter(tags__id__in=[self.a_tag.id])
            .distinct()
            .order_by("name")
        )
        with self.assertNumQueries(2):
            products = list(qs)
            _ = [(p.category.name, list(p.tags.all())) for p in products]
