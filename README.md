# Material Catalog — Django Take-Home Assignment

A Django-based construction material catalog built for electrical and mechanical
trade contractors. Allows purchasing agents and field teams to search and filter
products by name, description, category, and tags.

---

## Tech Stack

- Python 3.12
- Django 5.2
- SQLite (development)

---

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/pet-proj/material_catalog.git
cd material-catalog
```

### 2. Create and Activate Virtual Environment

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
py -m venv venv
venv\Scripts\activate.bat
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Migrations

This will create the database tables and automatically populate
them with sample data (5 categories, 10 tags, 20 products):

```bash
python manage.py migrate
```

### 5. Create a Superuser (for Admin access)

```bash
python manage.py createsuperuser
```

### 6. Run the Development Server

```bash
python manage.py runserver
```

---

## Access the Application

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:8000/` | Product search and filter page |
| `http://127.0.0.1:8000/admin/` | Django admin panel |

---

## Sample Data

Sample data is loaded automatically via a data migration
(`0002_seed_initial_data.py`) when you run `python manage.py migrate`.
No manual data entry is required.

| Model | Count | Examples |
|-------|-------|---------|
| Categories | 5 | Electrical Wiring, Conduit & Fittings, Circuit Protection |
| Tags | 10 | in-stock, UL-listed, prefab-ready, outdoor-rated |
| Products | 20 | 12 AWG THHN Copper Wire, 20A GFCI Breaker, LED High Bay Light |

---

## Features

### Search
- Search products by **name** or **description** using case-insensitive matching

### Filter
- Filter by **category** via dropdown
- Filter by **tags** via checkboxes (supports multiple tag selection)

### Combined Queries
- All filters can be combined simultaneously
- Active filters are displayed above results
- Result count updates dynamically
- One-click clear to reset all filters

### Favourites *(feature/favourites)*
- Authenticated users can mark any product as a favourite
- A dedicated favourites page lists all saved items

### Saved Filters *(feature/saved-filters)*
- Authenticated users can save a named combination of search query, category, and tags
- Saved filters appear in a sidebar and can be re-applied in one click

---

## Feature Branches

Additional features are developed on separate branches to demonstrate
incremental implementation:

| Branch | Purpose |
|--------|---------|
| `feature/favourites` | Users can save individual products to a personal favourites list for quick access |
| `feature/saved-filters` | Users can save a named search + filter combination and re-apply it in one click |
| `feature/tests` | Unit tests covering product filtering logic and pagination behaviour |
| `updated_search` *(merged)* | Query performance optimisation — replaced N+1 patterns with `select_related` / `prefetch_related` |

---

## Data Models

### Category
```python
class Category(models.Model):
    name = models.CharField(max_length=100)
```

### Tag
```python
class Tag(models.Model):
    name = models.CharField(max_length=100)
```

### Product
```python
class Product(models.Model):
    name            = models.CharField(max_length=200)
    sku             = models.CharField(max_length=50, unique=True)
    description     = models.TextField()
    unit_of_measure = models.CharField(max_length=20, choices=UNIT_CHOICES)
    category        = models.ForeignKey(Category, on_delete=models.CASCADE)
    tags            = models.ManyToManyField(Tag, blank=True)
```

### Relationships
- Product → Category: **Many-to-One** (ForeignKey)
- Product → Tags: **Many-to-Many**

---

## Django Query Proficiency

The view demonstrates the following ORM techniques:

| Technique | Purpose |
|-----------|---------|
| `Q objects` | OR logic across name and description fields |
| `select_related('category')` | Eliminates N+1 queries on ForeignKey |
| `prefetch_related('tags')` | Eliminates N+1 queries on ManyToMany |
| `tags__id__in` | Filtering across ManyToMany relationships |
| `.distinct()` | Prevents duplicate rows from JOIN on tags |
| Chained `.filter()` | Dynamic query building based on user input |

### N+1 Query Problem
Without `select_related` and `prefetch_related`, a page of 20 products
would fire 41 separate database queries (1 for products + 20 for
categories + 20 for tags). With these optimizations, it fires exactly
3 queries regardless of result size.

### Inline Code Commentary
`catalog/views.py` contains detailed inline comments explaining each ORM
decision as it is made — including the SQL each clause compiles to, why
`.distinct()` is required on the tag JOIN, and Django's lazy evaluation
model. Each filter block also includes a concrete suggested improvement
(e.g. `SearchVector` / `SearchQuery` for full-text search, `django-mptt`
for hierarchical categories, chained `.filter()` for AND tag logic) so
the code is self-documenting beyond what this README covers.

---

## Future Optimizations

1. **Database Indexes** — add `db_index=True` to frequently filtered fields
   (e.g. `Product.name`, `Product.category`) to speed up `WHERE` clauses
   significantly at 100k+ records.

2. **Caching** — Categories and tags are stable data that rarely change
   and are loaded on every request. In a high-traffic environment these
   would be cached using Django's cache framework with Redis as the backend.
   Cache invalidation would be handled via Django signals (`post_save` /
   `post_delete`) to ensure stale data is never served. Product search
   results would **not** be cached due to the high number of possible filter
   permutations resulting in a very low cache hit rate.

3. **Full-Text Search** — `icontains` uses `SQL LIKE '%term%'` which cannot
   use indexes and performs a full table scan. At scale, replace with
   `SearchVector` / `SearchQuery` (PostgreSQL only) or a dedicated engine
   such as Elasticsearch or Meilisearch.

4. **AND Tag Logic** — current tag filtering uses OR logic (products matching
   any selected tag are returned). AND logic (all selected tags must match)
   can be achieved by chaining individual `.filter()` calls, which generates
   a separate JOIN per tag.

---

## Assumptions

- SQLite is used for simplicity in development. In production, PostgreSQL
  would be the recommended database, particularly to leverage full-text
  search capabilities via `django.contrib.postgres`.
- Tag filtering uses OR logic — products matching any selected tag are
  returned. AND logic (all tags must match) is listed as a future
  enhancement.
- Styling is intentionally minimal per assignment requirements. The focus
  is on functionality and query implementation.
- SKU is included on the Product model as it is a standard field in
  construction material procurement systems and relevant to Remarcable's
  domain.
- In a production environment, sensitive settings such as `SECRET_KEY` 
and `DEBUG` would be managed via environment variables using a 
`.env` file, not hardcoded in `settings.py`.

---

## AI Usage Attribution

This project was developed with AI assistance (Claude by Anthropic) for:
- Initial project structure and boilerplate setup
- Sample data generation (product names, SKUs, descriptions)
- README formatting and documentation structure

All Django models, query logic, ORM optimization techniques, and
architectural decisions were written, reviewed, and are fully understood
by the author.
---