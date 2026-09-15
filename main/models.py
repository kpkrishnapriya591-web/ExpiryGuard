from django.db import models


class Product(models.Model):

    product_name = models.CharField(
        max_length=200
    )

    category = models.CharField(
        max_length=100
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    unit = models.CharField(
        max_length=50,
        default='Pieces'
    )

    batch_number = models.CharField(
        max_length=100,
        blank=True
    )

    supplier = models.CharField(
        max_length=200,
        blank=True
    )

    manufacture_date = models.DateField(
        null=True,
        blank=True
    )

    expiry_date = models.DateField()

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    location = models.CharField(
        max_length=100,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.product_name