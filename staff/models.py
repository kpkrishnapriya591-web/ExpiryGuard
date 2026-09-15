from django.db import models

from django.utils import timezone
class Product(models.Model):
    name = models.CharField(max_length=200)

    barcode = models.CharField(
        max_length=100,
        unique=True
    )

    brand = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    manufacturer = models.CharField(
        max_length=300,
        blank=True,
        null=True
    )

    category = models.CharField(
        max_length=300,
        blank=True,
        null=True
    )

    quantity = models.IntegerField(
        default=0
    )

    unit = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    batch_number = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )

    manufacture_date = models.DateField(
        blank=True,
        null=True
    )

    expiry_date = models.DateField(
        blank=True,
        null=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    image_url = models.URLField(
        max_length=500,
        blank=True,
        null=True
    )

    ingredients = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
    default=timezone.now
)

    def __str__(self):
        return f"{self.name} - {self.barcode}"