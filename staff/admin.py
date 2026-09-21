from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "expiry_date",
    )

    search_fields = (
        "name",
    )

    list_filter = (
        "expiry_date",
    )