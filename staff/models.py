from django.db import models


class Product(models.Model):

    name = models.CharField(max_length=200)

    barcode = models.CharField(
        max_length=100,
        unique=True
    )

    batch_number = models.CharField(
        max_length=100,
        blank=True
    )

    category = models.CharField(
        max_length=100,
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
        default=0
    )

    stock_quantity = models.IntegerField(
        default=0
    )

    def __str__(self):
        return self.name