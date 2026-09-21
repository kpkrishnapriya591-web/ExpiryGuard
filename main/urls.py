from django.urls import path
from . import views


urlpatterns = [

    # =========================
    # ADMIN LOGIN
    # =========================
    path(
        "",
        views.login_page,
        name="login"
    ),

    # =========================
    # HOME
    # =========================
    path(
        "home/",
        views.home,
        name="home"
    ),

   

   

    # =========================
    # NOTIFICATIONS
    # =========================
    path(
        "notifications/",
        views.notifications,
        name="notifications"
    ),

    # =========================
    # STAFF MANAGEMENT
    # =========================
    path(
        "add-staff/",
        views.add_staff,
        name="add_staff"
    ),

    path(
        "staff-management/",
        views.staff_management,
        name="staff_management"
    ),

    path(
        "staff-management/update/<int:staff_id>/",
        views.update_staff,
        name="update_staff"
    ),
path(
    "products/update/<int:product_id>/",
    views.update_product,
    name="admin_product_update"
),
  path(
    "staff-management/delete/<int:staff_id>/",
    views.delete_staff,
    name="delete_staff"
),

    # =========================
    # PRODUCT MANAGEMENT
    # =========================
   path(
    "products/",
    views.manage_products,
    name="manage_products"
),
path(
    "products/view/<int:product_id>/",
    views.view_product,
    name="view_product"
),

  path("add-product/", views.add_product, name="admin_add_product"),

    path(
        "product-status/",
        views.product_status,
        name="product_status"
    ),

    

    # =========================
    # ACCOUNT
    # =========================
    path(
        "account/",
        views.account,
        name="account"
    ),
path(
    "products/delete/<int:product_id>/",
    views.delete_product,
    name="delete_product"
),
    # =========================
    # LOGOUT
    # =========================
    path(
        "logout/",
        views.logout_page,
        name="logout"
    ),
]