from django import forms
from .models import Product


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product

        fields = [
            'product_name',
            'barcode',
            'batch_number',
            'quantity',
            'manufacturing_date',
            'expiry_date',
        ]

        widgets = {
            'manufacturing_date': forms.DateInput(
                attrs={'type': 'date'}
            ),

            'expiry_date': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }