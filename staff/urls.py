from django.urls import path
from . import views


urlpatterns = [

    path("login/", views.staff_login, name="staff_login"),
    path("signup/", views.staff_signup, name="staff_signup"),
    path("logout/", views.staff_logout, name="staff_logout"),

    path("home/", views.staff_home, name="staff_home"),

    path("dashboard/", views.staff_dashboard, name="staff_dashboard"),

    path("products/add/", views.add_product, name="add_product"),

    path("products/", views.staff_products, name="staff_products"),

    path(
    "products/update/<int:product_id>/",
    views.update_product,
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
        name="staff_expiry_dashboard"
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

    path(
    "expiry-simulator/",
    views.expiry_simulator,
    name="expiry_simulator"
),
]