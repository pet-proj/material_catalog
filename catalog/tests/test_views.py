from django.test import TestCase
from django.urls import reverse

from catalog.models import Category, Product, Tag


class ProductListViewTests(TestCase):
    """Tests for the product_list view: response, filtering, and template output."""

    @classmethod
    def setUpTestData(cls):
        Product.objects.all().delete()
        Category.objects.all().delete()
        Tag.objects.all().delete()

        cls.cat_elec = Category.objects.create(name="Electrical")
        cls.cat_tools = Category.objects.create(name="Tools")

        cls.tag_stock = Tag.objects.create(name="in-stock")
        cls.tag_outdoor = Tag.objects.create(name="outdoor-rated")
        cls.tag_bulk = Tag.objects.create(name="bulk-discount")

        # "power" appears in p_drill's NAME and p_conduit's DESCRIPTION for OR-logic testing.
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

        cls.url = reverse("catalog:product_list")

    # -- Response & Template --

    def test_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "catalog/product_list.html")

    def test_context_contains_required_keys(self):
        response = self.client.get(self.url)
        for key in ("products", "page_obj", "categories", "tags", "query", "selected_category", "selected_tags"):
            self.assertIn(key, response.context)

    # -- Text Search --

    def test_search_filters_by_name(self):
        response = self.client.get(self.url, {"q": "wire"})
        pks = {p.pk for p in response.context["products"]}
        self.assertEqual(pks, {self.p_wire.pk})

    def test_search_filters_by_description(self):
        response = self.client.get(self.url, {"q": "protection"})
        pks = {p.pk for p in response.context["products"]}
        self.assertEqual(pks, {self.p_breaker.pk})

    def test_search_empty_returns_all_products(self):
        response = self.client.get(self.url, {"q": ""})
        self.assertEqual(len(response.context["products"]), 4)

    def test_search_no_match_shows_no_results_message(self):
        response = self.client.get(self.url, {"q": "xyznotfound"})
        self.assertContains(response, "No products found")

    # -- Category Filter --

    def test_category_filter_returns_matching_products(self):
        response = self.client.get(self.url, {"category": self.cat_elec.id})
        pks = {p.pk for p in response.context["products"]}
        self.assertEqual(pks, {self.p_wire.pk, self.p_breaker.pk})

    def test_category_filter_excludes_other_categories(self):
        response = self.client.get(self.url, {"category": self.cat_tools.id})
        pks = {p.pk for p in response.context["products"]}
        self.assertEqual(pks, {self.p_drill.pk, self.p_conduit.pk})

    def test_invalid_category_id_returns_empty(self):
        response = self.client.get(self.url, {"category": 99999})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["products"]), 0)
        self.assertContains(response, "No products found")

    # -- Tag Filter --

    def test_single_tag_filter(self):
        response = self.client.get(self.url, {"tags": self.tag_stock.id})
        pks = {p.pk for p in response.context["products"]}
        self.assertEqual(pks, {self.p_wire.pk, self.p_breaker.pk})

    def test_multiple_tags_use_or_logic(self):
        # tag_stock → wire, breaker; tag_bulk → drill, conduit → all 4
        response = self.client.get(self.url, {"tags": [self.tag_stock.id, self.tag_bulk.id]})
        pks = {p.pk for p in response.context["products"]}
        self.assertEqual(pks, {self.p_wire.pk, self.p_breaker.pk, self.p_drill.pk, self.p_conduit.pk})

    def test_tag_filter_no_duplicate_products(self):
        # p_conduit has both tag_outdoor and tag_bulk; must appear exactly once
        response = self.client.get(self.url, {"tags": [self.tag_outdoor.id, self.tag_bulk.id]})
        product_pks = [p.pk for p in response.context["products"]]
        self.assertEqual(product_pks.count(self.p_conduit.pk), 1)

    # -- Active Filters Display --

    def test_no_active_filters_section_without_params(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, 'class="active-filters"')

    def test_active_filters_section_shown_when_searching(self):
        response = self.client.get(self.url, {"q": "wire"})
        self.assertContains(response, 'class="active-filters"')

    def test_active_filters_section_shown_when_category_selected(self):
        response = self.client.get(self.url, {"category": self.cat_elec.id})
        self.assertContains(response, 'class="active-filters"')

    def test_results_count_reflects_filtered_results(self):
        response = self.client.get(self.url, {"q": "wire"})
        self.assertEqual(response.context["page_obj"].paginator.count, 1)


class ProductListPaginationTests(TestCase):
    """Tests for pagination behaviour with more than one page of products."""

    @classmethod
    def setUpTestData(cls):
        Product.objects.all().delete()
        Category.objects.all().delete()
        Tag.objects.all().delete()

        cat = Category.objects.create(name="General")
        # 12 products → page 1 = 10, page 2 = 2
        for i in range(12):
            Product.objects.create(
                name=f"Product {i:02d}",
                sku=f"P-{i:03d}",
                description="generic item",
                category=cat,
            )
        cls.url = reverse("catalog:product_list")

    def test_first_page_shows_ten_products(self):
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["products"]), 10)

    def test_second_page_shows_remaining_products(self):
        response = self.client.get(self.url, {"page": 2})
        self.assertEqual(len(response.context["products"]), 2)

    def test_out_of_range_page_returns_last_page(self):
        # Paginator.get_page() clamps safely instead of raising
        response = self.client.get(self.url, {"page": 999})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["products"]), 2)

    def test_next_link_present_on_first_page(self):
        response = self.client.get(self.url)
        self.assertContains(response, "page=2")

    def test_no_next_link_on_last_page(self):
        response = self.client.get(self.url, {"page": 2})
        self.assertNotContains(response, "page=3")

    def test_pagination_link_preserves_search_param(self):
        # All 12 products match "Product"; next-page link must include q= param
        response = self.client.get(self.url, {"q": "Product"})
        self.assertContains(response, "q=Product")
