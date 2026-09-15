from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'product_name',
        'category',
        'quantity',
        'unit',
        'batch_number',
        'supplier',
        'manufacture_date',
        'expiry_date',
        'price',
        'location',
        'created_at',
    )

    search_fields = (
        'product_name',
        'category',
        'batch_number',
        'supplier',
        'location',
    )

    list_filter = (
        'category',
        'unit',
        'manufacture_date',
        'expiry_date',
    )

    ordering = (
        '-created_at',
    )

    list_per_page = 20