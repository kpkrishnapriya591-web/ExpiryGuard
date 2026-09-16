from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=200)

    barcode = models.CharField(
        max_length=100,
        unique=True
    )

    batch_number = models.CharField(max_length=100)

    manufacture_date = models.DateField()

    expiry_date = models.DateField()

    category = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    quantity = models.IntegerField(default=0)

    unit = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.name} - {self.barcode}"