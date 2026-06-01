from django.conf import settings
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
        ('each', 'Each'),
        ('box', 'Box'),
        ('spool', 'Spool'),
        ('roll', 'Roll'),
        ('pair', 'Pair'),
        ('set', 'Set'),
    ]

    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    unit_of_measure = models.CharField(max_length=20, choices=UNIT_CHOICES, default='each')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    tags = models.ManyToManyField(Tag, blank=True, related_name='products')

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(unit_of_measure__in=['each', 'box', 'spool', 'roll', 'pair', 'set']),
                name='valid_unit_of_measure',
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Favourite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favourites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favourited_by')

    class Meta:
        unique_together = ('user', 'product')