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
    # DASHBOARD
    # =========================
    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),

    # =========================
    # REPORTS
    # =========================
    path(
        "reports/",
        views.reports,
        name="reports"
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
        "add-product/",
        views.add_product,
        name="add_product"
    ),

    path(
        "product-status/",
        views.product_status,
        name="product_status"
    ),

    # =========================
    # ACTIVITY LOG
    # =========================
    path(
        "activity-log/",
        views.activity_log,
        name="activity_log"
    ),

    # =========================
    # ACCOUNT
    # =========================
    path(
        "account/",
        views.account,
        name="account"
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