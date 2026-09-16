# ============================================================
# STAFF / VIEWS.PY
# EXPIRYGUARD
# ============================================================

from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Product


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

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(
                request,
                user
            )

            return redirect(
                "staff_home"
            )

        return render(
            request,
            "staff/staff_login.html",
            {
                "error":
                    "Invalid username or password."
            }
        )

    return render(
        request,
        "staff/staff_login.html"
    )


# ============================================================
# STAFF SIGNUP
# ============================================================

def staff_signup(request):

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

        if not username or not password:

            return render(
                request,
                "staff/staff_signup.html",
                {
                    "error":
                        "Username and password are required."
                }
            )

        if password != confirm_password:

            return render(
                request,
                "staff/staff_signup.html",
                {
                    "error":
                        "Passwords do not match."
                }
            )

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

        return redirect(
            "staff_login"
        )

    return render(
        request,
        "staff/staff_signup.html"
    )


# ============================================================
# STAFF LOGOUT
# ============================================================

def staff_logout(request):

    logout(request)

    return redirect(
        "staff_login"
    )


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

        "products":
            products,

        "total_products":
            total_products,

        "expired_products":
            expired_products,

        "near_expiry_products":
            near_expiry_products,

        "safe_products":
            safe_products,
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

        "products":
            products,

        "total_products":
            total_products,

        "expired_products":
            expired_products,

        "near_expiry_products":
            near_expiry_products,

        "safe_products":
            safe_products,
    }

    return render(
        request,
        "staff/staff_dashboard.html",
        context
    )


# ============================================================
# ADD PRODUCT
# ============================================================

def add_product(request):

    check = staff_login_required(request)

    if check:
        return check

    if request.method == "POST":

        # ----------------------------------------------------
        # GET FORM DATA
        # ----------------------------------------------------

        name = request.POST.get(
            "name",
            ""
        ).strip()

        barcode = request.POST.get(
            "barcode",
            ""
        ).strip()

        batch_number = request.POST.get(
            "batch_number",
            ""
        ).strip()

        category = request.POST.get(
            "category",
            ""
        ).strip()

        manufacture_date = request.POST.get(
            "manufacture_date"
        ) or None

        expiry_date = request.POST.get(
            "expiry_date"
        ) or None

        price = request.POST.get(
            "price"
        ) or None

        quantity = request.POST.get(
            "quantity"
        ) or 0

        unit = request.POST.get(
            "unit",
            ""
        ).strip()

        # ----------------------------------------------------
        # REQUIRED FIELD CHECK
        # ----------------------------------------------------

        if not name or not barcode or not batch_number:

            return render(
                request,
                "staff/add_product.html",
                {
                    "error":
                        "Product Name, Barcode and Batch Number are required."
                }
            )

        if not manufacture_date or not expiry_date:

            return render(
                request,
                "staff/add_product.html",
                {
                    "error":
                        "Manufacture Date and Expiry Date are required."
                }
            )

        if not price:

            return render(
                request,
                "staff/add_product.html",
                {
                    "error":
                        "MRP / Price is required."
                }
            )

        # ----------------------------------------------------
        # DUPLICATE BARCODE CHECK
        # ----------------------------------------------------

        if Product.objects.filter(
            barcode=barcode
        ).exists():

            return render(
                request,
                "staff/add_product.html",
                {
                    "error":
                        "This barcode already exists."
                }
            )

        # ----------------------------------------------------
        # QUANTITY CONVERSION
        # ----------------------------------------------------

        try:

            quantity = int(quantity)

        except (
            ValueError,
            TypeError
        ):

            quantity = 0

        # ----------------------------------------------------
        # PRICE CONVERSION
        # ----------------------------------------------------

        try:

            price = float(price)

        except (
            ValueError,
            TypeError
        ):

            return render(
                request,
                "staff/add_product.html",
                {
                    "error":
                        "Please enter a valid price."
                }
            )

        # ----------------------------------------------------
        # SAVE PRODUCT
        # ----------------------------------------------------

        Product.objects.create(

            name=name,

            barcode=barcode,

            batch_number=batch_number,

            manufacture_date=manufacture_date,

            expiry_date=expiry_date,

            category=category,

            quantity=quantity,

            unit=unit,

            price=price
        )

        messages.success(
            request,
            "Product added successfully."
        )

        return redirect(
            "staff_product_status"
        )

    return render(
        request,
        "staff/add_product.html"
    )


# ============================================================
# STAFF PRODUCTS
# ============================================================

def staff_products(request):

    check = staff_login_required(request)

    if check:
        return check

    products = Product.objects.all().order_by(
        "-id"
    )

    today = date.today()

    for product in products:

        product.expiry_status = (
            calculate_expiry_status(
                product.expiry_date
            )
        )

    return render(
        request,
        "staff/manage_products.html",
        {
            "products":
                products,

            "today":
                today,
        }
    )


# ============================================================
# CALCULATE EXPIRY STATUS
# ============================================================

def calculate_expiry_status(expiry_date):

    if not expiry_date:

        return "UNKNOWN"

    today = date.today()

    if expiry_date < today:

        return "EXPIRED"

    elif expiry_date <= today + timedelta(days=30):

        return "NEAR EXPIRY"

    else:

        return "SAFE"


# ============================================================
# UPDATE STAFF PRODUCT
# ============================================================

def update_staff_product(
    request,
    product_id
):

    check = staff_login_required(request)

    if check:
        return check

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        # ----------------------------------------------------
        # BASIC DETAILS
        # ----------------------------------------------------

        product.name = request.POST.get(
            "name",
            product.name
        ).strip()

        product.barcode = request.POST.get(
            "barcode",
            product.barcode
        ).strip()

        product.category = request.POST.get(
            "category",
            product.category or ""
        ).strip()

        product.batch_number = request.POST.get(
            "batch_number",
            product.batch_number
        ).strip()

        product.unit = request.POST.get(
            "unit",
            product.unit or ""
        ).strip()

        # ----------------------------------------------------
        # QUANTITY
        # ----------------------------------------------------

        quantity_text = request.POST.get(
            "quantity",
            product.quantity
        )

        try:

            product.quantity = int(
                quantity_text
            )

        except (
            ValueError,
            TypeError
        ):

            pass

        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        price_text = request.POST.get(
            "price",
            ""
        ).strip()

        if price_text:

            try:

                product.price = float(
                    price_text
                )

            except (
                ValueError,
                TypeError
            ):

                pass

        # ----------------------------------------------------
        # MANUFACTURE DATE
        # ----------------------------------------------------

        manufacture_date = request.POST.get(
            "manufacture_date"
        )

        if manufacture_date:

            try:

                product.manufacture_date = (
                    datetime.strptime(
                        manufacture_date,
                        "%Y-%m-%d"
                    ).date()
                )

            except ValueError:

                pass

        # ----------------------------------------------------
        # EXPIRY DATE
        # ----------------------------------------------------

        expiry_date = request.POST.get(
            "expiry_date"
        )

        if expiry_date:

            try:

                product.expiry_date = (
                    datetime.strptime(
                        expiry_date,
                        "%Y-%m-%d"
                    ).date()
                )

            except ValueError:

                pass

        # ----------------------------------------------------
        # SAVE UPDATED PRODUCT
        # ----------------------------------------------------

        product.save()

        messages.success(
            request,
            "Product updated successfully."
        )

        return redirect(
            "staff_products"
        )

    return render(
        request,
        "staff/update_product.html",
        {
            "product":
                product
        }
    )


# ============================================================
# DELETE STAFF PRODUCT
# ============================================================

@require_POST
def delete_staff_product(
    request,
    product_id
):

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

        if not product.expiry_date:

            product.expiry_status = "UNKNOWN"

            unknown_products.append(
                product
            )

        elif product.expiry_date < today:

            product.expiry_status = "EXPIRED"

            expired_products.append(
                product
            )

        elif product.expiry_date <= (
            today + timedelta(days=30)
        ):

            product.expiry_status = "NEAR EXPIRY"

            near_expiry_products.append(
                product
            )

        else:

            product.expiry_status = "SAFE"

            safe_products.append(
                product
            )

    context = {

        "products":
            products,

        "expired_products":
            expired_products,

        "near_expiry_products":
            near_expiry_products,

        "safe_products":
            safe_products,

        "unknown_products":
            unknown_products,

        "expired_count":
            len(expired_products),

        "near_expiry_count":
            len(near_expiry_products),

        "safe_count":
            len(safe_products),

        "unknown_count":
            len(unknown_products),

        "today":
            today,
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

    products = Product.objects.all()

    today = date.today()

    expired_products = []

    near_expiry_products = []

    safe_products = []

    unknown_products = []

    for product in products:

        if not product.expiry_date:

            product.expiry_status = "UNKNOWN"

            unknown_products.append(
                product
            )

        elif product.expiry_date < today:

            product.expiry_status = "EXPIRED"

            expired_products.append(
                product
            )

        elif product.expiry_date <= (
            today + timedelta(days=30)
        ):

            product.expiry_status = "NEAR EXPIRY"

            near_expiry_products.append(
                product
            )

        else:

            product.expiry_status = "SAFE"

            safe_products.append(
                product
            )

    context = {

        "products":
            products,

        "today":
            today,

        "expired_products":
            expired_products,

        "near_expiry_products":
            near_expiry_products,

        "safe_products":
            safe_products,

        "unknown_products":
            unknown_products,

        "expired_count":
            len(expired_products),

        "near_expiry_count":
            len(near_expiry_products),

        "safe_count":
            len(safe_products),

        "unknown_count":
            len(unknown_products),
    }

    return render(
        request,
        "staff/product_status.html",
        context
    )


# ============================================================
# STAFF NOTIFICATIONS
# ============================================================

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

    notifications = []

    # --------------------------------------------------------
    # EXPIRED PRODUCTS
    # --------------------------------------------------------

    for product in expired_products:

        product_name = str(product)

        notifications.append({

            "type":
                "expired",

            "title":
                "Product Expired",

            "message":
                f"{product_name} has expired.",

            "product":
                product,
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

            "type":
                "warning",

            "title":
                "Product Expiring Soon",

            "message":
                f"{product_name} will expire "
                f"in {days_left} day(s).",

            "product":
                product,
        })

    return render(
        request,
        "staff/notifications.html",
        {
            "notifications":
                notifications,

            "products":
                products,

            "expired_products":
                expired_products,

            "near_expiry_products":
                near_expiry_products,

            "safe_products":
                safe_products,

            "expired_count":
                expired_products.count(),

            "near_expiry_count":
                near_expiry_products.count(),

            "safe_count":
                safe_products.count(),
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
            "user":
                user
        }
    )