from django.urls import path
from . import views


urlpatterns = [

    # ============================================================
    # STAFF LOGIN / SIGNUP / LOGOUT
    # ============================================================

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


    # ============================================================
    # STAFF HOME
    # ============================================================

    path(
        "home/",
        views.staff_home,
        name="staff_home"
    ),


    # ============================================================
    # STAFF DASHBOARD
    # ============================================================

    path(
        "dashboard/",
        views.staff_dashboard,
        name="staff_dashboard"
    ),


    # ============================================================
    # ADD PRODUCT
    # ============================================================

    path(
        "products/add/",
        views.add_product,
        name="add_product"
    ),


    # ============================================================
    # PRODUCT LIST
    # ============================================================

    path(
        "products/",
        views.staff_products,
        name="staff_products"
    ),


    # ============================================================
    # UPDATE PRODUCT
    # ============================================================

    path(
        "products/update/<int:product_id>/",
        views.update_staff_product,
        name="update_product"
    ),


    # ============================================================
    # DELETE PRODUCT
    # ============================================================

    path(
        "products/delete/<int:product_id>/",
        views.delete_staff_product,
        name="delete_product"
    ),


    # ============================================================
    # EXPIRY DASHBOARD
    # ============================================================

    path(
        "expiry-dashboard/",
        views.staff_expiry_dashboard,
        name="staff_expiry_dashboard"
    ),


    # ============================================================
    # PRODUCT STATUS
    # ============================================================

    path(
        "product-status/",
        views.staff_product_status,
        name="staff_product_status"
    ),


    # ============================================================
    # NOTIFICATIONS
    # ============================================================

    path(
        "notifications/",
        views.staff_notifications,
        name="staff_notifications"
    ),


    # ============================================================
    # ACCOUNT
    # ============================================================

    path(
        "account/",
        views.staff_account,
        name="staff_account"
    ),
]