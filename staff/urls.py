from django.urls import path
from . import views

urlpatterns = [

    path(
        "login/",
        views.staff_login,
        name="staff_login"
    ),

    path(
        "signup/",
        views.staff_signup,
        name="staff_signup"
    ),

    path(
        "logout/",
        views.staff_logout,
        name="staff_logout"
    ),

    path(
        "home/",
        views.staff_home,
        name="staff_home"
    ),

    path(
        "dashboard/",
        views.staff_dashboard,
        name="staff_dashboard"
    ),

    # ONE SCANNER PAGE
    path(
        "products/add/",
        views.add_product,
        name="add_product"
    ),

    # Barcode
    path(
        "barcode-info/",
        views.get_product_from_barcode,
        name="get_product_from_barcode"
    ),

    # Same camera → OCR
    path(
        "ocr-extract/",
        views.extract_product_details_from_image,
        name="extract_product_details_from_image"
    ),

    # Save
    path(
        "barcode-save/",
        views.save_scanned_product,
        name="save_scanned_product"
    ),

    # Product listing
    path(
        "products/",
        views.staff_products,
        name="staff_products"
    ),

    path(
        "products/update/<int:product_id>/",
        views.update_staff_product,
        name="update_product"
    ),

    path(
        "products/delete/<int:product_id>/",
        views.delete_staff_product,
        name="delete_product"
    ),

    path(
        "expiry-dashboard/",
        views.staff_expiry_dashboard,
        name="expiry_dashboard"
    ),

    path(
        "product-status/",
        views.staff_product_status,
        name="staff_product_status"
    ),

    path(
        "notifications/",
        views.staff_notifications,
        name="staff_notifications"
    ),

    path(
        "account/",
        views.staff_account,
        name="staff_account"
    ),
]