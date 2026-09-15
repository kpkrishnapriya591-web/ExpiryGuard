from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User


# =========================
# ADMIN LOGIN
# =========================
def login_page(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            # Create login session
            login(request, user)

            # IMPORTANT:
            # After successful login → HOME PAGE
            return redirect("home")

        else:

            return render(
                request,
                "main/login.html",
                {
                    "error": "Invalid username or password"
                }
            )

    return render(
        request,
        "main/login.html"
    )


# =========================
# HOME
# =========================
def home(request):

    if not request.user.is_authenticated:
        return redirect("login")

    return render(
        request,
        "main/home.html"
    )


# =========================
# DASHBOARD
# =========================
def dashboard(request):

    if not request.user.is_authenticated:
        return redirect("login")

    return render(
        request,
        "main/dashboard.html"
    )


# =========================
# REPORTS
# =========================
def reports(request):

    if not request.user.is_authenticated:
        return redirect("login")

    return render(
        request,
        "main/reports.html"
    )


# =========================
# NOTIFICATIONS
# =========================
def notifications(request):

    if not request.user.is_authenticated:
        return redirect("login")

    return render(
        request,
        "main/notifications.html"
    )


# =========================
# PRODUCT MANAGEMENT
# =========================
def manage_products(request):

    if not request.user.is_authenticated:
        return redirect("login")

    return render(
        request,
        "main/manage_products.html"
    )


# =========================
# ADD PRODUCT
# =========================
def add_product(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if request.method == "POST":

        return redirect("manage_products")

    return render(
        request,
        "main/add_product.html"
    )


# =========================
# VIEW PRODUCT
# =========================
def view_product(request, product_id):

    if not request.user.is_authenticated:
        return redirect("login")

    return render(
        request,
        "main/manage_products.html"
    )


# =========================
# UPDATE PRODUCT
# =========================
def update_product(request, product_id):

    if not request.user.is_authenticated:
        return redirect("login")

    return redirect("manage_products")


# =========================
# DELETE PRODUCT
# =========================
def delete_product(request, product_id):

    if not request.user.is_authenticated:
        return redirect("login")

    if request.method == "POST":
        pass

    return redirect("manage_products")


# =========================
# PRODUCT STATUS
# =========================
def product_status(request):

    if not request.user.is_authenticated:
        return redirect("login")

    return render(
        request,
        "main/product_status.html"
    )


# =========================
# ADD STAFF
# =========================
def add_staff(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if request.method == "POST":

        return redirect("staff_management")

    return render(
        request,
        "main/add_staff.html"
    )


# =========================
# STAFF MANAGEMENT
# =========================
def staff_management(request):

    if not request.user.is_authenticated:
        return redirect("login")

    staff_members = []

    return render(
        request,
        "main/staff_management.html",
        {
            "staff_members": staff_members
        }
    )


# =========================
# UPDATE STAFF
# =========================
def update_staff(request, staff_id):

    if not request.user.is_authenticated:
        return redirect("login")

    return redirect("staff_management")


# =========================
# DELETE STAFF
# =========================
def delete_staff(request, staff_id):

    if not request.user.is_authenticated:
        return redirect("login")

    if request.method == "POST":
        pass

    return redirect("staff_management")


# =========================
# ACTIVITY LOG
# =========================
def activity_log(request):

    if not request.user.is_authenticated:
        return redirect("login")

    return render(
        request,
        "main/activity_log.html"
    )


# =========================
# ACCOUNT
# =========================
def account(request):

    if not request.user.is_authenticated:
        return redirect("login")

    return render(
        request,
        "main/account.html"
    )


# =========================
# LOGOUT
# =========================
def logout_page(request):

    logout(request)

    return redirect("login")