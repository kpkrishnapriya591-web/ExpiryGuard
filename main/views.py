from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages


# =========================
# LOGIN
# =========================
def login_page(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect('home')

        else:

            messages.error(
                request,
                'Invalid username or password.'
            )

            return redirect('login')

    return render(
        request,
        'main/login.html'
    )


# =========================
# SIGNUP
# =========================
def signup_page(request):

    if request.method == 'GET':

        return render(
            request,
            'main/signup.html'
        )

    if request.method == 'POST':

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if not username or not password or not confirm_password:

            messages.error(
                request,
                'Please fill all required fields.'
            )

            return redirect('signup')

        if password != confirm_password:

            messages.error(
                request,
                'Passwords do not match.'
            )

            return redirect('signup')

        if User.objects.filter(username=username).exists():

            messages.error(
                request,
                'Username already exists.'
            )

            return redirect('signup')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.save()

        messages.success(
            request,
            'Account created successfully. Please login.'
        )

        return redirect('login')

    return redirect('signup')


# =========================
# HOME
# =========================
def home(request):

    if not request.user.is_authenticated:
        return redirect('login')

    return render(
        request,
        'main/home.html'
    )


# =========================
# DASHBOARD
# =========================
def dashboard(request):

    if not request.user.is_authenticated:
        return redirect('login')

    return render(
        request,
        'main/dashboard.html'
    )


# =========================
# REPORTS
# =========================
def reports(request):

    if not request.user.is_authenticated:
        return redirect('login')

    return render(
        request,
        'main/reports.html'
    )


# =========================
# NOTIFICATIONS
# =========================
def notifications(request):

    if not request.user.is_authenticated:
        return redirect('login')

    return render(
        request,
        'main/notifications.html'
    )


# =========================
# PRODUCT MANAGEMENT
# =========================
def manage_products(request):

    if not request.user.is_authenticated:
        return redirect('login')

    return render(
        request,
        'main/manage_products.html'
    )

def add_staff(request):
    return render(request, 'main/add_staff.html')
def add_product(request):

    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':

        return redirect('manage_products')

  
    return render(request, 'main/add_product.html')
    


def view_product(request, product_id):

    if not request.user.is_authenticated:
        return redirect('login')

    return render(
        request,
        'main/manage_products.html'
    )


def update_product(request, product_id):

    if not request.user.is_authenticated:
        return redirect('login')

    return redirect('manage_products')


def delete_product(request, product_id):

    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        pass

    return redirect('manage_products')


# =========================
# PRODUCT STATUS
# =========================
def product_status(request):

    if not request.user.is_authenticated:
        return redirect('login')

    return render(
        request,
        'main/product_status.html'
    )


# =========================
# STAFF MANAGEMENT
# =========================
def staff_management(request):

    if not request.user.is_authenticated:
        return redirect('login')

    staff_members = []

    return render(
        request,
        'main/staff_management.html',
        {
            'staff_members': staff_members
        }
    )


def add_staff(request):

    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':

        return redirect('staff_management')

    return render(
        request,
        'main/add_staff.html'
    )


def update_staff(request, staff_id):

    if not request.user.is_authenticated:
        return redirect('login')

    return redirect('staff_management')


def delete_staff(request, staff_id):

    if not request.user.is_authenticated:
        return redirect('login')

    if request.method == 'POST':
        pass

    return redirect('staff_management')


# =========================
# ACTIVITY LOG
# =========================
def activity_log(request):

    if not request.user.is_authenticated:
        return redirect('login')

    return render(
        request,
        'main/activity_log.html'
    )


# =========================
# ACCOUNT
# =========================
def account(request):

    if not request.user.is_authenticated:
        return redirect('login')

    return render(
        request,
        'main/account.html'
    )


# =========================
# LOGOUT
# =========================
def logout_page(request):

    logout(request)

    return redirect('login')