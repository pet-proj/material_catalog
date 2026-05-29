from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100)

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
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    tags = models.ManyToManyField(Tag, blank=True, related_name='products')

    def __str__(self):
        return f"{self.name} ({self.sku})"