from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
import math
from .models import Product
from django.shortcuts import render
from .models import Product
from main.models import Product as MainProduct
# ============================================================
# COMMON LOGIN CHECK
# ============================================================

def staff_login_required(request):
    if not request.user.is_authenticated:
        return redirect("staff_login")

    return None


# ============================================================
# STAFF LOGIN
# ============================================================

def staff_login(request):

    if request.user.is_authenticated:
        return redirect("staff_home")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect("staff_home")

        else:

            return render(
                request,
                "staff/staff_login.html",
                {
                    "error": "Invalid username or password"
                }
            )

    return render(
        request,
        "staff/staff_login.html"
    )
def staff_signup(request):

    if request.method == "POST":

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

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

        # ----------------------------------------------------
        # REQUIRED FIELD CHECK
        # ----------------------------------------------------

        if not username or not password:

            return render(
                request,
                "staff/staff_signup.html",
                {
                    "error":
                        "Username and password are required."
                }
            )

        # ----------------------------------------------------
        # PASSWORD CHECK
        # ----------------------------------------------------

        if password != confirm_password:

            return render(
                request,
                "staff/staff_signup.html",
                {
                    "error":
                        "Passwords do not match."
                }
            )

        # ----------------------------------------------------
        # USERNAME DUPLICATE CHECK
        # ----------------------------------------------------

        if User.objects.filter(
            username=username
        ).exists():

            return render(
                request,
                "staff/staff_signup.html",
                {
                    "error":
                        "Username already exists."
                }
            )

        # ----------------------------------------------------
        # CREATE USER
        # ----------------------------------------------------

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )

        user.is_staff = False
        user.save()

        messages.success(
            request,
            "Staff account created successfully."
        )

        return redirect("staff_login")

    return render(
        request,
        "staff/staff_signup.html"
    )


# ============================================================
# STAFF LOGOUT
# ============================================================

def staff_logout(request):

    logout(request)

    return redirect("staff_login")


# ============================================================
# STAFF HOME
# ============================================================

def staff_home(request):

    check = staff_login_required(request)

    if check:
        return check

    products = Product.objects.all()

    today = date.today()

    total_products = products.count()

    expired_products = products.filter(
        expiry_date__lt=today
    ).count()

    near_expiry_products = products.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=30)
    ).count()

    safe_products = products.filter(
        expiry_date__gt=today + timedelta(days=30)
    ).count()

    context = {
        "products": products,
        "total_products": total_products,
        "expired_products": expired_products,
        "near_expiry_products": near_expiry_products,
        "safe_products": safe_products,
    }

    return render(
        request,
        "staff/staff_home.html",
        context
    )


# ============================================================
# STAFF DASHBOARD
# ============================================================

def staff_dashboard(request):

    check = staff_login_required(request)

    if check:
        return check

    products = Product.objects.all()

    today = date.today()

    total_products = products.count()

    expired_products = products.filter(
        expiry_date__lt=today
    ).count()

    near_expiry_products = products.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=30)
    ).count()

    safe_products = products.filter(
        expiry_date__gt=today + timedelta(days=30)
    ).count()

    context = {
        "products": products,
        "total_products": total_products,
        "expired_products": expired_products,
        "near_expiry_products": near_expiry_products,
        "safe_products": safe_products,
    }

    return render(
        request,
        "staff/staff_dashboard.html",
        context
    )



def calculate_expiry_status(expiry_date):

    if not expiry_date:
        return "UNKNOWN"

    today = date.today()

    if expiry_date < today:
        return "EXPIRED"

    if expiry_date <= today + timedelta(days=30):
        return "NEAR EXPIRY"

    return "SAFE"


# ============================================================
# STAFF PRODUCTS
# ============================================================

def staff_products(request):

    check = staff_login_required(request)

    if check:
        return check

    products = Product.objects.all().order_by("-id")

    today = date.today()

    for product in products:

        product.expiry_status = calculate_expiry_status(
            product.expiry_date
        )

    return render(
        request,
        "staff/manage_products.html",
        {
            "products": products,
            "today": today,
        }
    )


# ============================================================
# UPDATE STAFF PRODUCT
# ============================================================

# ============================================================
# UPDATE PRODUCT
# ============================================================

def update_product(request, product_id):

    check = staff_login_required(request)
    if check:
        return check

    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        barcode = request.POST.get("barcode", "").strip()
        batch_number = request.POST.get("batch_number", "").strip()
        category = request.POST.get("category", "").strip()
        price = request.POST.get("price", "0")
        stock_quantity = request.POST.get("stock_quantity", "0")
        manufacture_date = request.POST.get("manufacture_date") or None
        expiry_date = request.POST.get("expiry_date") or None

        if not name:
            messages.error(request, "Product name is required.")
            return redirect("update_product", product_id=product.id)

        if not barcode:
            messages.error(request, "Barcode is required.")
            return redirect("update_product", product_id=product.id)

        # Check duplicate barcode
        duplicate = Product.objects.filter(
            barcode=barcode
        ).exclude(
            id=product.id
        ).first()

        if duplicate:
            messages.error(
                request,
                "This barcode already exists for another product."
            )
            return redirect("update_product", product_id=product.id)

        try:
            price_value = Decimal(price)

            if price_value < 0:
                raise ValueError

        except (InvalidOperation, ValueError, TypeError):
            messages.error(request, "Please enter a valid price.")
            return redirect("update_product", product_id=product.id)

        try:
            stock_value = int(stock_quantity)

            if stock_value < 0:
                raise ValueError

        except (ValueError, TypeError):
            messages.error(request, "Please enter a valid stock quantity.")
            return redirect("update_product", product_id=product.id)

        # Update staff product
        product.name = name
        product.barcode = barcode
        product.batch_number = batch_number
        product.category = category
        product.price = price_value
        product.stock_quantity = stock_value
        product.manufacture_date = manufacture_date
        product.expiry_date = expiry_date

        product.save()

        # Also update main product
        main_product = MainProduct.objects.filter(
            barcode=barcode
        ).first()

        if main_product:

            main_product.product_name = name
            main_product.barcode = barcode
            main_product.batch_number = batch_number
            main_product.category = category
            main_product.quantity = stock_value
            main_product.price = price_value
            main_product.manufacture_date = manufacture_date
            main_product.expiry_date = expiry_date

            main_product.save()

        messages.success(
            request,
            f"{name} updated successfully."
        )

        return redirect("staff_product_status")

    return render(
        request,
        "staff/update_product.html",
        {
            "product": product
        }
    )
@require_POST
def delete_staff_product(request, product_id):

    check = staff_login_required(request)

    if check:
        return check

    product = get_object_or_404(
        Product,
        id=product_id
    )

    product.delete()

    messages.success(
        request,
        "Product deleted successfully."
    )

    return redirect(
        "staff_products"
    )


# ============================================================
# STAFF EXPIRY DASHBOARD
# ============================================================

def staff_expiry_dashboard(request):

    check = staff_login_required(request)

    if check:
        return check

    products = Product.objects.all()

    today = date.today()

    expired_products = []
    near_expiry_products = []
    safe_products = []
    unknown_products = []

    for product in products:

        status = calculate_expiry_status(
            product.expiry_date
        )

        product.expiry_status = status

        if status == "UNKNOWN":

            unknown_products.append(product)

        elif status == "EXPIRED":

            expired_products.append(product)

        elif status == "NEAR EXPIRY":

            near_expiry_products.append(product)

        else:

            safe_products.append(product)

    context = {
        "products": products,
        "expired_products": expired_products,
        "near_expiry_products": near_expiry_products,
        "safe_products": safe_products,
        "unknown_products": unknown_products,
        "expired_count": len(expired_products),
        "near_expiry_count": len(near_expiry_products),
        "safe_count": len(safe_products),
        "unknown_count": len(unknown_products),
        "today": today,
    }

    return render(
        request,
        "staff/expiry_dashboard.html",
        context
    )


# ============================================================
# STAFF PRODUCT STATUS
# ============================================================
def staff_product_status(request):

    check = staff_login_required(request)

    if check:
        return check

    products = Product.objects.all().order_by("expiry_date")

    today = date.today()

    product_data = []

    for product in products:

        days_left = (product.expiry_date - today).days

        if days_left < 0:
            status = "Expired"
            status_class = "expired"

        elif days_left == 0:
            status = "Expires Today"
            status_class = "critical"

        elif days_left <= 7:
            status = "Expiring Soon"
            status_class = "warning"

        else:
            status = "Safe"
            status_class = "safe"

        product_data.append({
            "product": product,
            "days_left": days_left,
            "status": status,
            "status_class": status_class,
        })

    return render(
        request,
        "staff/product_status.html",
        {
            "product_data": product_data,
            "today": today,
        }
    )

def staff_notifications(request):

    check = staff_login_required(request)

    if check:
        return check

    today = date.today()

    products = Product.objects.all()

    expired_products = products.filter(
        expiry_date__lt=today
    )

    near_expiry_products = products.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=30)
    )

    safe_products = products.filter(
        expiry_date__gt=today + timedelta(days=30)
    )

    unknown_products = products.filter(
        expiry_date__isnull=True
    )

    notifications = []

    # --------------------------------------------------------
    # EXPIRED PRODUCTS
    # --------------------------------------------------------

    for product in expired_products:

        product_name = str(product)

        notifications.append({
            "type": "expired",
            "title": "Product Expired",
            "message":
                f"{product_name} has expired.",
            "product": product,
        })

    # --------------------------------------------------------
    # NEAR EXPIRY PRODUCTS
    # --------------------------------------------------------

    for product in near_expiry_products:

        product_name = str(product)

        days_left = (
            product.expiry_date - today
        ).days

        notifications.append({
            "type": "warning",
            "title": "Product Expiring Soon",
            "message":
                f"{product_name} will expire "
                f"in {days_left} day(s).",
            "product": product,
        })

    # --------------------------------------------------------
    # UNKNOWN EXPIRY
    # --------------------------------------------------------

    for product in unknown_products:

        notifications.append({
            "type": "unknown",
            "title": "Expiry Date Missing",
            "message":
                f"{str(product)} does not have an expiry date.",
            "product": product,
        })

    return render(
        request,
        "staff/notifications.html",
        {
            "notifications": notifications,
            "products": products,
            "expired_products": expired_products,
            "near_expiry_products": near_expiry_products,
            "safe_products": safe_products,
            "unknown_products": unknown_products,
            "expired_count": expired_products.count(),
            "near_expiry_count": near_expiry_products.count(),
            "safe_count": safe_products.count(),
            "unknown_count": unknown_products.count(),
        }
    )


# ============================================================
# STAFF ACCOUNT
# ============================================================

def staff_account(request):

    check = staff_login_required(request)

    if check:
        return check

    user = request.user

    if request.method == "POST":

        user.first_name = request.POST.get(
            "first_name",
            ""
        ).strip()

        user.last_name = request.POST.get(
            "last_name",
            ""
        ).strip()

        user.email = request.POST.get(
            "email",
            ""
        ).strip()

        user.save()

        messages.success(
            request,
            "Account updated successfully."
        )

        return redirect(
            "staff_account"
        )

    return render(
        request,
        "staff/account.html",
        {
            "user": user
        }
    )


# ============================================================
# EXPIRY SIMULATOR
# ============================================================







def products(request):
    products = Product.objects.all()

    today = date.today()

    for product in products:
        
        remaining_days = (product.expiry_date - today).days

        # Daily sale calculation
        if remaining_days > 0 and product.quantity > 0:
            daily_sale = product.quantity / remaining_days

            
            daily_sale = int(daily_sale) if daily_sale == int(daily_sale) else int(daily_sale) + 1
        else:
            daily_sale = 0

     
        product.remaining_days = max(remaining_days, 0)
        product.daily_sale = daily_sale

        # Status
        if remaining_days < 0:
            product.expiry_status = "Expired"
        elif remaining_days == 0:
            product.expiry_status = "Expires Today"
        elif remaining_days <= 7:
            product.expiry_status = "Expiring Soon"
        else:
            product.expiry_status = "Safe"

    return render(request, "staff/products.html", {
        "products": products
    })
def expiry_simulator(request):

    # Get all products
    products = Product.objects.all().order_by("expiry_date")

    product_data = []

    today = date.today()

    for product in products:

        # Calculate remaining days
        days_until_expiry = (
            product.expiry_date - today
        ).days

        # Get current stock
        stock = product.stock_quantity or 0

        # ------------------------------------------------
        # PRODUCT NOT EXPIRED
        # ------------------------------------------------
        if days_until_expiry > 0 and stock > 0:

            # Minimum number of units to sell per day
            required_daily_sale = math.ceil(
                stock / days_until_expiry
            )

            expiry_message = (
                f"🛒 To reduce wastage, sell at least "
                f"{required_daily_sale} unit(s) per day before expiry."
            )

        # ------------------------------------------------
        # EXPIRING TODAY
        # ------------------------------------------------
        elif days_until_expiry == 0:

            required_daily_sale = stock

            expiry_message = (
                "⚠️ This product expires today. "
                "Sell the remaining stock immediately."
            )

        # ------------------------------------------------
        # ALREADY EXPIRED
        # ------------------------------------------------
        elif days_until_expiry < 0:

            required_daily_sale = 0

            expiry_message = (
                "❌ This product has already expired."
            )

        # ------------------------------------------------
        # NO STOCK
        # ------------------------------------------------
        else:

            required_daily_sale = 0

            expiry_message = (
                "No stock available."
            )

        # Add product information
        product_data.append({
            "product": product,
            "days_until_expiry": days_until_expiry,
            "required_daily_sale": required_daily_sale,
            "expiry_message": expiry_message,
        })

    # IMPORTANT:
    # This return is required
    return render(
        request,
        "staff/expiry_simulator.html",
        {
            "products": products,
            "product_data": product_data,
        }
    )


# ============================================================
# ADD PRODUCT
# STAFF + ADMIN
# ================================================

def add_product(request):

    check = staff_login_required(request)

    if check:
        return check

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        barcode = request.POST.get("barcode", "").strip()
        batch_number = request.POST.get("batch_number", "").strip()
        category = request.POST.get("category", "").strip()

        manufacture_date = (
            request.POST.get("manufacture_date") or None
        )

        expiry_date = request.POST.get("expiry_date") or None

        price = request.POST.get("price") or "0"

        quantity = request.POST.get("quantity") or "0"

        unit = request.POST.get(
            "unit",
            "Pieces"
        ).strip()

        supplier = request.POST.get(
            "supplier",
            ""
        ).strip()

        location = request.POST.get(
            "location",
            ""
        ).strip()

        description = request.POST.get(
            "description",
            ""
        ).strip()

        # ----------------------------------------------------
        # REQUIRED FIELD CHECKS
        # ----------------------------------------------------

        if not name:

            messages.error(
                request,
                "Product name is required."
            )

            return redirect("add_product")

        if not barcode:

            messages.error(
                request,
                "Barcode is required."
            )

            return redirect("add_product")

        if not expiry_date:

            messages.error(
                request,
                "Expiry date is required."
            )

            return redirect("add_product")

        # ----------------------------------------------------
        # QUANTITY
        # ----------------------------------------------------

        try:

            stock_quantity = int(quantity)

            if stock_quantity < 0:
                raise ValueError

        except (ValueError, TypeError):

            messages.error(
                request,
                "Please enter a valid quantity."
            )

            return redirect("add_product")

        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        try:

            price_value = Decimal(price)

            if price_value < 0:
                raise ValueError

        except (InvalidOperation, ValueError, TypeError):

            messages.error(
                request,
                "Please enter a valid price."
            )

            return redirect("add_product")

        # ----------------------------------------------------
        # DUPLICATE BARCODE - STAFF
        # ----------------------------------------------------

        if Product.objects.filter(
            barcode=barcode
        ).exists():

            messages.error(
                request,
                "A product with this barcode already exists."
            )

            return redirect("add_product")

        # ----------------------------------------------------
        # SAVE IN STAFF DATABASE
        # ----------------------------------------------------

        Product.objects.create(

            name=name,

            barcode=barcode,

            batch_number=batch_number,

            category=category,

            manufacture_date=manufacture_date,

            expiry_date=expiry_date,

            price=price_value,

            stock_quantity=stock_quantity
        )

        # ----------------------------------------------------
        # SAVE SAME PRODUCT IN MAIN / ADMIN DATABASE
        # ----------------------------------------------------

        MainProduct.objects.create(

            product_name=name,

            barcode=barcode,

            batch_number=batch_number,

            category=category,

            quantity=stock_quantity,

            unit=unit,

            supplier=supplier,

            price=price_value,

            manufacture_date=manufacture_date,

            expiry_date=expiry_date,

            location=location,

            description=description
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------
        
               # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        messages.success(
            request,
            f"{name} added successfully."
        )

        return redirect("expiry_simulator")

    return render(
        request,
        "staff/add_product.html"
    )
