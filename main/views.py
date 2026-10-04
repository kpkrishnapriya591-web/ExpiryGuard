from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404

from django.views.decorators.http import require_POST
from .models import Product


# =========================================================
# ADMIN LOGIN
# =========================================================

def login_page(request):

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

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


# =========================================================
# HOME
# =========================================================

def home(request):

    if not request.user.is_authenticated:
        return redirect("login")

    return render(
        request,
        "main/home.html"
    )

# =========================================================
# NOTIFICATIONS
# =========================================================

from datetime import date

def notifications(request):

    if not request.user.is_authenticated:
        return redirect("login")

    today = date.today()

    notifications = []

    products = Product.objects.all()

    for product in products:

        if not product.expiry_date:
            continue

        days_left = (product.expiry_date - today).days

        if days_left < 0:
            notifications.append({
                "product": product,
                "message": "Product has expired",
                "type": "expired"
            })

        elif days_left <= 7:
            notifications.append({
                "product": product,
                "message": f"Product expires in {days_left} days",
                "type": "warning"
            })

    return render(
        request,
        "main/notifications.html",
        {
            "notifications": notifications
        }
    )
def manage_products(request):

    if not request.user.is_authenticated:
        return redirect("login")

    products = Product.objects.all().order_by("-id")

    return render(
        request,
        "main/manage_products.html",
        {
            "products": products
        }
    )


# =========================================================
# VIEW PRODUCT
# =========================================================

def view_product(request, product_id):

    if not request.user.is_authenticated:
        return redirect("login")

    product = get_object_or_404(
        Product,
        id=product_id
    )

    return render(
        request,
        "main/view_product.html",
        {
            "product": product
        }
    )


# =========================================================
# UPDATE PRODUCT
# =========================================================

def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        product.product_name = request.POST.get("product_name")
        product.category = request.POST.get("category")
        product.quantity = request.POST.get("quantity")
        
        product.batch_number = request.POST.get("batch_number")
      
        product.manufacture_date = request.POST.get("manufacture_date")
        product.expiry_date = request.POST.get("expiry_date")
        product.price = request.POST.get("price")
        

        if hasattr(product, "barcode"):
            product.barcode = request.POST.get("barcode")

        product.save()

        messages.success(request, "Product updated successfully.")
        return redirect("manage_products")

    return render(request, "main/update_product.html", {
        "product": product
    })

# =========================================================
# ADD STAFF
# =========================================================

def add_staff(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if request.method == "POST":

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        first_name = request.POST.get(
            "first_name",
            ""
        ).strip()

        last_name = request.POST.get(
            "last_name",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        # Required fields
        if not username or not password or not confirm_password:

            return render(
                request,
                "main/add_staff.html",
                {
                    "error":
                    "Username, password and confirm password are required."
                }
            )

        # Password match
        if password != confirm_password:

            return render(
                request,
                "main/add_staff.html",
                {
                    "error": "Passwords do not match."
                }
            )

        # Username already exists
        if User.objects.filter(
            username=username
        ).exists():

            return render(
                request,
                "main/add_staff.html",
                {
                    "error": "Username already exists."
                }
            )

        # Create staff account
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )

        # Normal staff account
        user.is_staff = False
        user.is_superuser = False
        user.save()

        return redirect("staff_management")

    return render(
        request,
        "main/add_staff.html"
    )


# =========================================================
# STAFF MANAGEMENT
# =========================================================

def staff_management(request):

    if not request.user.is_authenticated:
        return redirect("login")

    staff_members = User.objects.filter(
        is_staff=False,
        is_superuser=False
    )

    return render(
        request,
        "main/staff_management.html",
        {
            "staff_members": staff_members
        }
    )


# =========================================================
# UPDATE STAFF
# =========================================================

def update_staff(request, staff_id):

    if not request.user.is_authenticated:
        return redirect("login")

    staff = get_object_or_404(
        User,
        id=staff_id,
        is_staff=False,
        is_superuser=False
    )

    if request.method == "POST":

        staff.first_name = request.POST.get(
            "first_name",
            ""
        ).strip()

        staff.last_name = request.POST.get(
            "last_name",
            ""
        ).strip()

        staff.email = request.POST.get(
            "email",
            ""
        ).strip()

        staff.save()

        return redirect("staff_management")

    return render(
        request,
        "main/update_staff.html",
        {
            "staff": staff
        }
    )




def account(request):

    if not request.user.is_authenticated:
        return redirect("login")

    return render(
        request,
        "main/account.html"
    )


# =========================================================
# LOGOUT
# =========================================================

def logout_page(request):

    logout(request)

    return redirect("login")


# =========================================================
# PRODUCT STATUS
# =========================================================

from datetime import date
from django.shortcuts import render, redirect
from .models import Product


def product_status(request):

    if not request.user.is_authenticated:
        return redirect("login")

    today = date.today()

    safe_products = []
    near_expiry_products = []
    expired_products = []

    products = Product.objects.all()

    for product in products:

        if not product.expiry_date:
            continue

        days_left = (product.expiry_date - today).days

        if days_left < 0:

            expired_products.append(product)

        elif days_left <= 7:

            near_expiry_products.append(product)

        else:

            safe_products.append(product)

    return render(
        request,
        "main/product_status.html",
        {
            "safe_products": safe_products,
            "near_expiry_products": near_expiry_products,
            "expired_products": expired_products,
        }
    )


# =========================================================
# ADD PRODUCT
# =========================================================



def add_product(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if request.method == "POST":

        # -----------------------------------------
        # Get form values
        # -----------------------------------------

        product_name = request.POST.get(
            "product_name",
            ""
        ).strip()

        category = request.POST.get(
            "category",
            ""
        ).strip()

        barcode = request.POST.get(
            "barcode",
            ""
        ).strip()

        quantity = request.POST.get(
            "quantity"
        ) or 1

        unit = request.POST.get(
            "unit",
            "Pieces"
        ).strip() or "Pieces"

        batch_number = request.POST.get(
            "batch_number",
            ""
        ).strip()

        supplier = request.POST.get(
            "supplier",
            ""
        ).strip()

        manufacture_date = (
            request.POST.get(
                "manufacture_date"
            )
            or None
        )

        expiry_date = (
            request.POST.get(
                "expiry_date"
            )
            or None
        )

        price = (
            request.POST.get(
                "price"
            )
            or None
        )

        location = request.POST.get(
            "location",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        # -----------------------------------------
        # Save product
        # -----------------------------------------

        Product.objects.create(

            product_name=product_name,

            category=category,

            barcode=barcode,

            quantity=quantity,

            unit=unit,

            batch_number=batch_number,

            supplier=supplier,

            manufacture_date=manufacture_date,

            expiry_date=expiry_date,

            price=price,

            location=location,

            # IMPORTANT:
            # Never send None to NOT NULL description field
            description=description or ""
        )

        # -----------------------------------------
        # After saving
        # -----------------------------------------

        return redirect(
            "manage_products"
        )

    # GET request
    return render(
        request,
        "main/add_product.html"
    )





@require_POST
def delete_staff(request, staff_id):
    try:
        staff = User.objects.get(
            id=staff_id,
            is_staff=False,
            is_superuser=False
        )

        username = staff.username
        staff.delete()

        messages.success(
            request,
            f"Staff '{username}' deleted successfully."
        )

    except User.DoesNotExist:
        messages.error(
            request,
            "Staff member not found."
        )

    return redirect("staff_management")

@require_POST
def delete_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    product.delete()

    messages.success(request, "Product deleted successfully.")

    return redirect("manage_products")