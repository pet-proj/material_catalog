from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    UNIT_CHOICES = [
        ("each", "Each"),
        ("box", "Box"),
        ("spool", "Spool"),
        ("roll", "Roll"),
        ("pair", "Pair"),
        ("set", "Set"),
    ]

    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    unit_of_measure = models.CharField(
        max_length=20, choices=UNIT_CHOICES, default="each"
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    unit_of_measure__in=["each", "box", "spool", "roll", "pair", "set"]
                ),
                name="valid_unit_of_measure",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"


class SavedFilter(models.Model):
    """
    Persists a named search filter combination for reuse.

    Allows purchasing agents to save frequently used filter presets
    such as 'Project 42 Electrical Supplies' or 'Prefab Ready Items'
    and reload them with a single click.

    Relationships:
    - category: optional ForeignKey — a saved filter may or may not
      specify a category. SET_NULL ensures saved filters survive
      category deletion.
    - tags: optional ManyToMany — a saved filter can include
      zero or more tags.
    """

    name = models.CharField(max_length=100)
    query = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="saved_filters",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="saved_filters")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
