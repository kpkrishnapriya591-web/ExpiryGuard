import re
import requests
import pytesseract
import cv2
import numpy as np

from datetime import date, datetime, timedelta
from PIL import Image

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Product


# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# ============================================================
# STAFF LOGIN
# ============================================================

def staff_login(request):

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

            login(request, user)

            return redirect("staff_home")

        messages.error(
            request,
            "Invalid username or password."
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

        email = request.POST.get(
            "email",
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

        if not username or not password:

            messages.error(
                request,
                "Username and password are required."
            )

            return redirect("staff_signup")

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return redirect("staff_signup")

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                "Username already exists."
            )

            return redirect("staff_signup")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.save()

        messages.success(
            request,
            "Account created successfully. Please login."
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


# ============================================================
# ADD PRODUCT PAGE
# ============================================================

def add_product(request):

    return render(
        request,
        "staff/add_product.html"
    )


# ============================================================
# BARCODE → ONLINE PRODUCT INFORMATION
# OPEN FOOD FACTS
# ============================================================

def get_product_from_barcode(request):

    if request.method != "GET":

        return JsonResponse(
            {
                "success": False,
                "message": "Only GET request is allowed."
            },
            status=405
        )

    barcode = request.GET.get(
        "barcode",
        ""
    ).strip()

    if not barcode:

        return JsonResponse(
            {
                "success": False,
                "message": "Barcode is required."
            },
            status=400
        )

    # --------------------------------------------------------
    # First check local database
    # --------------------------------------------------------

    existing_product = Product.objects.filter(
        barcode=barcode
    ).first()

    if existing_product:

        return JsonResponse(
            {
                "success": True,
                "source": "database",

                "name":
                    existing_product.name or "",

                "barcode":
                    existing_product.barcode or "",

                "brand":
                    existing_product.brand or "",

                "manufacturer":
                    existing_product.manufacturer or "",

                "category":
                    existing_product.category or "",

                "quantity":
                    existing_product.quantity,

                "unit":
                    existing_product.unit or "",

                "batch_number":
                    existing_product.batch_number or "",

                "manufacture_date":
                    (
                        existing_product.manufacture_date.isoformat()
                        if existing_product.manufacture_date
                        else ""
                    ),

                "expiry_date":
                    (
                        existing_product.expiry_date.isoformat()
                        if existing_product.expiry_date
                        else ""
                    ),

                "price":
                    (
                        str(existing_product.price)
                        if hasattr(existing_product, "price")
                        else "0"
                    ),

                "description":
                    existing_product.description or "",

                "ingredients":
                    existing_product.ingredients or "",

                "image_url":
                    existing_product.image_url or "",
            }
        )

    # --------------------------------------------------------
    # Open Food Facts
    # --------------------------------------------------------

    url = (
        "https://world.openfoodfacts.org/api/v2/product/"
        + barcode
    )

    try:

        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "ExpiryGuard/1.0"
            }
        )

        if response.status_code != 200:

            return JsonResponse(
                {
                    "success": False,
                    "message":
                        "Product not found online."
                }
            )

        data = response.json()

        if data.get("status") != 1:

            return JsonResponse(
                {
                    "success": False,
                    "message":
                        "Product not found online."
                }
            )

        product_data = data.get(
            "product",
            {}
        )

        product_name = (
            product_data.get("product_name")
            or product_data.get("product_name_en")
            or ""
        )

        brands = product_data.get(
            "brands",
            ""
        )

        categories = product_data.get(
            "categories",
            ""
        )

        manufacturers = product_data.get(
            "manufacturing_places",
            ""
        )

        quantity_text = product_data.get(
            "quantity",
            ""
        )

        image_url = (
            product_data.get(
                "image_front_url"
            )
            or product_data.get(
                "image_url"
            )
            or ""
        )

        ingredients = product_data.get(
            "ingredients_text",
            ""
        )

        generic_name = product_data.get(
            "generic_name",
            ""
        )

        return JsonResponse(
            {
                "success": True,
                "source": "open_food_facts",

                "name":
                    product_name,

                "barcode":
                    barcode,

                "brand":
                    brands,

                "manufacturer":
                    manufacturers,

                "category":
                    categories,

                "quantity":
                    0,

                "unit":
                    quantity_text,

                "batch_number":
                    "",

                "manufacture_date":
                    "",

                "expiry_date":
                    "",

                "price":
                    "",

                "description":
                    generic_name,

                "ingredients":
                    ingredients,

                "image_url":
                    image_url,
            }
        )

    except requests.RequestException as error:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Unable to connect to product service.",
                "error":
                    str(error)
            },
            status=500
        )

    except Exception as error:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Unexpected error while getting product information.",
                "error":
                    str(error)
            },
            status=500
        )


# ============================================================
# OCR TEXT NORMALIZATION
# ============================================================

def normalize_ocr_text(text):

    if not text:
        return ""

    text = text.upper()

    replacements = {

        "M8P": "MRP",
        "M8": "MR",
        "M.R.P": "MRP",
        "M R P": "MRP",

        "B8TCH": "BATCH",
        "BAT CH": "BATCH",

        "BATCH NO": "BATCH",
        "BATCHNO": "BATCH",

        "LOT NO": "LOT",

        "EXP.": "EXP",
        "EXPIRY": "EXP",
        "EXP DATE": "EXP",

        "MFG.": "MFG",
        "MFD.": "MFG",
        "MFD": "MFG",

        "R.S.": "RS",
        "R.S": "RS",
        "R S": "RS",
    }

    for old, new in replacements.items():

        text = text.replace(
            old,
            new
        )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# DATE PARSER
# ============================================================
def parse_ocr_date(text):

    if not text:
        return None

    text = str(text).upper().strip()

    replacements = {
        "O": "0",
        "I": "1",
        "L": "1",
        "|": "1",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(
        r"[^0-9./\-]",
        "",
        text
    )

    patterns = [
        r"^(\d{1,2})[./\-](\d{1,2})[./\-](\d{4})$",
        r"^(\d{1,2})[./\-](\d{1,2})[./\-](\d{2})$",
    ]

    for pattern in patterns:

        match = re.match(
            pattern,
            text
        )

        if not match:
            continue

        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3))

        if year < 100:
            year += 2000

        try:
            return date(
                year,
                month,
                day
            )

        except ValueError:
            continue

    return None
def extract_mfg_exp_from_text(text):

    manufacture_date = None
    expiry_date = None

    if not text:
        return None, None

    text = normalize_ocr_text(text)

    # MFG / MFD / MANUFACTURED
    mfg_patterns = [
        r"(?:MFG|MFD|MANUFACTURED|MANUFACTURING)"
        r"\s*(?:DATE|DT)?\s*[:.\-]?\s*"
        r"([0-9OIL]{1,2}[./\-][0-9OIL]{1,2}[./\-][0-9OIL]{2,4})",

        r"(?:MFG|MFD)"
        r"\s*[:.\-]?\s*"
        r"([0-9OIL]{1,2}[./\-][0-9OIL]{1,2}[./\-][0-9OIL]{2,4})",
    ]

    for pattern in mfg_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            manufacture_date = parse_ocr_date(
                match.group(1)
            )

            if manufacture_date:
                break

    # EXP / EXPIRY
    exp_patterns = [
        r"(?:EXP|EXPIRY|USE\s*BY|BEST\s*BEFORE)"
        r"\s*(?:DATE|DT)?\s*[:.\-]?\s*"
        r"([0-9OIL]{1,2}[./\-][0-9OIL]{1,2}[./\-][0-9OIL]{2,4})",

        r"(?:EXP|EXPIRY)"
        r"\s*[:.\-]?\s*"
        r"([0-9OIL]{1,2}[./\-][0-9OIL]{1,2}[./\-][0-9OIL]{2,4})",
    ]

    for pattern in exp_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            expiry_date = parse_ocr_date(
                match.group(1)
            )

            if expiry_date:
                break

    return (
        manufacture_date,
        expiry_date
    )
def extract_batch_from_text(text):

    if not text:
        return ""

    text = normalize_ocr_text(text)

    patterns = [

        r"\bBATCH\s*(?:NO|NUMBER)?\s*[:.\-]?\s*"
        r"([A-Z0-9][A-Z0-9./_-]{2,30})",

        r"\bB\s*[\.\-]?\s*NO\s*[:.\-]?\s*"
        r"([A-Z0-9][A-Z0-9./_-]{2,30})",

        r"\bLOT\s*(?:NO|NUMBER)?\s*[:.\-]?\s*"
        r"([A-Z0-9][A-Z0-9./_-]{2,30})",

        r"\bLOT\s*[:.\-]?\s*"
        r"([A-Z0-9][A-Z0-9./_-]{2,30})",

        r"\bBN\s*[:.\-]?\s*"
        r"([A-Z0-9][A-Z0-9./_-]{2,30})",

    ]

    for pattern in patterns:

        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE
        )

        for value in matches:

            value = clean_batch_number(
                value
            )

            if not value:
                continue

            if parse_ocr_date(value):
                continue

            if value.isdigit() and len(value) >= 6:
                continue

            return value

    return ""

def calculate_expiry_status(
    expiry_date
):

    if not expiry_date:

        return "UNKNOWN"

    today = date.today()

    if expiry_date < today:

        return "EXPIRED"

    days_left = (
        expiry_date - today
    ).days

    if days_left == 0:

        return "EXPIRES TODAY"

    if days_left <= 7:

        return "EXPIRING IN 7 DAYS"

    if days_left <= 15:

        return "EXPIRING IN 15 DAYS"

    if days_left <= 30:

        return "EXPIRING IN 30 DAYS"

    return "SAFE"


# ============================================================
# PREPARE MULTIPLE OCR IMAGES
# ============================================================

def prepare_ocr_images(image):

    images = []

    if image is None:
        return images

    if image.size == 0:
        return images

    # --------------------------------------------------------
    # Original
    # --------------------------------------------------------

    images.append(
        (
            "original",
            image.copy()
        )
    )

    # --------------------------------------------------------
    # Resize 3x
    # --------------------------------------------------------

    resized3 = cv2.resize(
        image,
        None,
        fx=3,
        fy=3,
        interpolation=cv2.INTER_CUBIC
    )

    images.append(
        (
            "resized3",
            resized3
        )
    )

    # --------------------------------------------------------
    # Resize 4x
    # --------------------------------------------------------

    resized4 = cv2.resize(
        image,
        None,
        fx=4,
        fy=4,
        interpolation=cv2.INTER_CUBIC
    )

    images.append(
        (
            "resized4",
            resized4
        )
    )

    # --------------------------------------------------------
    # Grayscale
    # --------------------------------------------------------

    gray = cv2.cvtColor(
        resized4,
        cv2.COLOR_BGR2GRAY
    )

    images.append(
        (
            "gray",
            gray
        )
    )

    # --------------------------------------------------------
    # Denoise
    # --------------------------------------------------------

    denoised = cv2.fastNlMeansDenoising(
        gray,
        None,
        10,
        7,
        21
    )

    images.append(
        (
            "denoised",
            denoised
        )
    )

    # --------------------------------------------------------
    # CLAHE
    # --------------------------------------------------------

    clahe = cv2.createCLAHE(
        clipLimit=3.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(
        denoised
    )

    images.append(
        (
            "enhanced",
            enhanced
        )
    )

    # --------------------------------------------------------
    # Sharpen
    # --------------------------------------------------------

    sharpen_kernel = np.array(
        [
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ]
    )

    sharpened = cv2.filter2D(
        enhanced,
        -1,
        sharpen_kernel
    )

    images.append(
        (
            "sharpened",
            sharpened
        )
    )

    # --------------------------------------------------------
    # OTSU
    # --------------------------------------------------------

    _, otsu = cv2.threshold(
        sharpened,
        0,
        255,
        cv2.THRESH_BINARY
        + cv2.THRESH_OTSU
    )

    images.append(
        (
            "otsu",
            otsu
        )
    )

    # --------------------------------------------------------
    # OTSU INVERSE
    # --------------------------------------------------------

    otsu_inverse = cv2.bitwise_not(
        otsu
    )

    images.append(
        (
            "otsu_inverse",
            otsu_inverse
        )
    )

    # --------------------------------------------------------
    # Adaptive
    # --------------------------------------------------------

    adaptive = cv2.adaptiveThreshold(
        sharpened,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        9
    )

    images.append(
        (
            "adaptive",
            adaptive
        )
    )

    # --------------------------------------------------------
    # Adaptive inverse
    # --------------------------------------------------------

    adaptive_inverse = cv2.bitwise_not(
        adaptive
    )

    images.append(
        (
            "adaptive_inverse",
            adaptive_inverse
        )
    )

    # --------------------------------------------------------
    # Important packet regions
    # --------------------------------------------------------

    h, w = resized4.shape[:2]

    # Bottom 50%
    bottom = resized4[
        int(h * 0.50):h,
        0:w
    ]

    images.append(
        (
            "bottom",
            bottom
        )
    )

    # Bottom 70%
    bottom_large = resized4[
        int(h * 0.30):h,
        0:w
    ]

    images.append(
        (
            "bottom_large",
            bottom_large
        )
    )

    # Middle-lower
    middle_lower = resized4[
        int(h * 0.30):int(h * 0.90),
        0:w
    ]

    images.append(
        (
            "middle_lower",
            middle_lower
        )
    )

    # Left lower
    left_lower = resized4[
        int(h * 0.40):h,
        0:int(w * 0.70)
    ]

    images.append(
        (
            "left_lower",
            left_lower
        )
    )

    # Right lower
    right_lower = resized4[
        int(h * 0.40):h,
        int(w * 0.30):w
    ]

    images.append(
        (
            "right_lower",
            right_lower
        )
    )

    return images


# ============================================================
# EXTRACT PRODUCT DETAILS
# ============================================================

def extract_product_details_from_text(
    text
):

    normalized = normalize_ocr_text(
        text
    )

    batch_number = extract_batch_from_text(
        normalized
    )

    manufacture_date, expiry_date = (
        extract_mfg_exp_from_text(
            normalized
        )
    )

    # --------------------------------------------------------
    # Fallback date extraction
    # --------------------------------------------------------

    if (
        manufacture_date is None
        or expiry_date is None
    ):

        fallback_mfg, fallback_exp = (
            fallback_mfg_exp(
                normalized
            )
        )

        if manufacture_date is None:

            manufacture_date = (
                fallback_mfg
            )

        if expiry_date is None:

            expiry_date = (
                fallback_exp
            )

    # --------------------------------------------------------
    # Price
    # --------------------------------------------------------

    price = extract_price_from_text(
        normalized
    )

    return {

        "batch_number":
            batch_number,

        "manufacture_date":
            (
                manufacture_date.isoformat()
                if manufacture_date
                else ""
            ),

        "expiry_date":
            (
                expiry_date.isoformat()
                if expiry_date
                else ""
            ),

        "price":
            price,

        "expiry_status":
            calculate_expiry_status(
                expiry_date
            ),
    }


# ============================================================
# OCR CAMERA IMAGE ENDPOINT
# ============================================================

@require_POST
def extract_product_details_from_image(
    request
):

    uploaded_file = request.FILES.get(
        "image"
    )

    if not uploaded_file:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "No camera image received."
            },
            status=400
        )

    try:

        # ----------------------------------------------------
        # Read uploaded camera image
        # ----------------------------------------------------

        pil_image = Image.open(
            uploaded_file
        ).convert("RGB")

        image_array = np.array(
            pil_image
        )

        image = cv2.cvtColor(
            image_array,
            cv2.COLOR_RGB2BGR
        )

        if image.size == 0:

            return JsonResponse(
                {
                    "success": False,
                    "message":
                        "Empty camera image."
                },
                status=400
            )

        # ----------------------------------------------------
        # Prepare OCR images
        # ----------------------------------------------------

        ocr_images = prepare_ocr_images(
            image
        )

        all_text = []

        seen_text = set()

        # ----------------------------------------------------
        # Tesseract PSM modes
        # ----------------------------------------------------

        psm_modes = [
            6,
            11,
            12,
            7,
            13
        ]

        for image_name, ocr_image in ocr_images:

            for psm in psm_modes:

                try:

                    config = (
                        f"--oem 3 --psm {psm}"
                    )

                    text = pytesseract.image_to_string(
                        ocr_image,
                        config=config,
                        lang="eng"
                    )

                    if not text:
                        continue

                    text = text.strip()

                    if not text:
                        continue

                    key = text.upper()

                    if key not in seen_text:

                        seen_text.add(
                            key
                        )

                        all_text.append(
                            text
                        )

                except Exception:

                    continue

        # ----------------------------------------------------
        # Combine OCR
        # ----------------------------------------------------

        combined_text = "\n".join(
            all_text
        )

        # ----------------------------------------------------
        # First extraction
        # ----------------------------------------------------

        details = extract_product_details_from_text(
            combined_text
        )

        # ====================================================
        # SECOND FOCUSED OCR PASS
        # ====================================================

        h, w = image.shape[:2]

        focused_regions = [

            # Bottom half
            image[
                int(h * 0.50):h,
                0:w
            ],

            # Bottom 70%
            image[
                int(h * 0.30):h,
                0:w
            ],

            # Left bottom
            image[
                int(h * 0.40):h,
                0:int(w * 0.70)
            ],

            # Right bottom
            image[
                int(h * 0.40):h,
                int(w * 0.30):w
            ],

            # Full image
            image
        ]

        focused_texts = []

        for region in focused_regions:

            if region is None:
                continue

            if region.size == 0:
                continue

            # ------------------------------------------------
            # Large resize
            # ------------------------------------------------

            enlarged = cv2.resize(
                region,
                None,
                fx=5,
                fy=5,
                interpolation=cv2.INTER_CUBIC
            )

            # ------------------------------------------------
            # Grayscale
            # ------------------------------------------------

            gray = cv2.cvtColor(
                enlarged,
                cv2.COLOR_BGR2GRAY
            )

            # ------------------------------------------------
            # CLAHE
            # ------------------------------------------------

            clahe = cv2.createCLAHE(
                clipLimit=4.0,
                tileGridSize=(8, 8)
            )

            gray = clahe.apply(
                gray
            )

            # ------------------------------------------------
            # Denoise
            # ------------------------------------------------

            gray = cv2.GaussianBlur(
                gray,
                (3, 3),
                0
            )

            # ------------------------------------------------
            # Sharpen
            # ------------------------------------------------

            sharpen_kernel = np.array(
                [
                    [0, -1, 0],
                    [-1, 5, -1],
                    [0, -1, 0]
                ]
            )

            sharp = cv2.filter2D(
                gray,
                -1,
                sharpen_kernel
            )

            versions = [
                gray,
                sharp
            ]

            # ------------------------------------------------
            # OTSU
            # ------------------------------------------------

            _, binary = cv2.threshold(
                sharp,
                0,
                255,
                cv2.THRESH_BINARY
                + cv2.THRESH_OTSU
            )

            versions.append(
                binary
            )

            # ------------------------------------------------
            # Adaptive threshold
            # ------------------------------------------------

            adaptive = cv2.adaptiveThreshold(
                sharp,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                41,
                11
            )

            versions.append(
                adaptive
            )

            # ------------------------------------------------
            # Inverted
            # ------------------------------------------------

            inverse = cv2.bitwise_not(
                binary
            )

            versions.append(
                inverse
            )

            for version in versions:

                for psm in [
                    6,
                    7,
                    11,
                    12
                ]:

                    try:

                        config = (
                            f"--oem 3 --psm {psm}"
                        )

                        text = pytesseract.image_to_string(
                            version,
                            config=config,
                            lang="eng"
                        )

                        if text and text.strip():

                            focused_texts.append(
                                text.strip()
                            )

                    except Exception:

                        continue

        # ----------------------------------------------------
        # Add focused OCR
        # ----------------------------------------------------

        if focused_texts:

            combined_text += (
                "\n"
                + "\n".join(
                    focused_texts
                )
            )

        # ----------------------------------------------------
        # Extract AGAIN
        # ----------------------------------------------------

        details = extract_product_details_from_text(
            combined_text
        )

        # ----------------------------------------------------
        # Final values
        # ----------------------------------------------------

        batch = details.get(
            "batch_number",
            ""
        )

        manufacture = details.get(
            "manufacture_date",
            ""
        )

        expiry = details.get(
            "expiry_date",
            ""
        )

        price = details.get(
            "price"
        )

        # ----------------------------------------------------
        # Final expiry status
        # ----------------------------------------------------

        expiry_object = None

        if expiry:

            try:

                expiry_object = datetime.strptime(
                    expiry,
                    "%Y-%m-%d"
                ).date()

            except ValueError:

                expiry_object = None

        status = calculate_expiry_status(
            expiry_object
        )

        # ----------------------------------------------------
        # Check if anything detected
        # ----------------------------------------------------

        detected_any = bool(
            batch
            or manufacture
            or expiry
            or price is not None
        )

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        return JsonResponse(
            {
                "success": True,

                "detected":
                    detected_any,

                "batch_number":
                    batch,

                "manufacture_date":
                    manufacture,

                "expiry_date":
                    expiry,

                "price":
                    price,

                "expiry_status":
                    status,

                "ocr_text":
                    combined_text,

                "detected_dates":
                    [
                        {
                            "text":
                                item["text"],

                            "date":
                                item["date"].isoformat()
                        }

                        for item
                        in find_date_candidates(
                            combined_text
                        )
                    ],

                "message":
                    (
                        "Product details detected."
                        if detected_any
                        else
                        "No Batch / MFG / EXP / MRP detected. "
                        "Move the camera closer to the printed "
                        "information area and capture again."
                    )
            }
        )

    except Exception as error:

        return JsonResponse(
            {
                "success": False,

                "message":
                    "OCR processing failed.",

                "error":
                    str(error)
            },
            status=500
        )


# ============================================================
# SAVE SCANNED PRODUCT
# ============================================================

@require_POST
def save_scanned_product(
    request
):

    barcode = request.POST.get(
        "barcode",
        ""
    ).strip()

    name = request.POST.get(
        "name",
        ""
    ).strip()

    if not barcode:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Barcode is required."
            },
            status=400
        )

    if not name:

        name = "Unknown Product"

    # --------------------------------------------------------
    # Date converter
    # --------------------------------------------------------

    def convert_date(value):

        if not value:
            return None

        value = value.strip()

        formats = [

            "%Y-%m-%d",

            "%d-%m-%Y",

            "%d/%m/%Y",

            "%d.%m.%Y",

        ]

        for fmt in formats:

            try:

                return datetime.strptime(
                    value,
                    fmt
                ).date()

            except ValueError:

                continue

        return None

    manufacture_date = convert_date(
        request.POST.get(
            "manufacture_date",
            ""
        )
    )

    expiry_date = convert_date(
        request.POST.get(
            "expiry_date",
            ""
        )
    )

    # --------------------------------------------------------
    # Basic fields
    # --------------------------------------------------------

    brand = request.POST.get(
        "brand",
        ""
    ).strip()

    manufacturer = request.POST.get(
        "manufacturer",
        ""
    ).strip()

    category = request.POST.get(
        "category",
        ""
    ).strip()

    unit = request.POST.get(
        "unit",
        ""
    ).strip()

    batch_number = request.POST.get(
        "batch_number",
        ""
    ).strip()

    description = request.POST.get(
        "description",
        ""
    ).strip()

    ingredients = request.POST.get(
        "ingredients",
        ""
    ).strip()

    image_url = request.POST.get(
        "image_url",
        ""
    ).strip()

    # --------------------------------------------------------
    # Quantity
    # --------------------------------------------------------

    quantity_text = request.POST.get(
        "quantity",
        "0"
    ).strip()

    try:

        quantity = int(
            quantity_text
        )

    except (
        ValueError,
        TypeError
    ):

        quantity = 0

    # --------------------------------------------------------
    # Price
    # --------------------------------------------------------

    price_text = request.POST.get(
        "price",
        ""
    ).strip()

    try:

        price = float(
            price_text
        ) if price_text else 0

    except (
        ValueError,
        TypeError
    ):

        price = 0

    # --------------------------------------------------------
    # Save / Update
    # --------------------------------------------------------

    product, created = (
        Product.objects.update_or_create(
            barcode=barcode,

            defaults={

                "name":
                    name,

                "brand":
                    brand,

                "manufacturer":
                    manufacturer,

                "category":
                    category,

                "quantity":
                    quantity,

                "unit":
                    unit,

                "batch_number":
                    batch_number,

                "manufacture_date":
                    manufacture_date,

                "expiry_date":
                    expiry_date,

                "description":
                    description,

                "ingredients":
                    ingredients,

                "image_url":
                    image_url,
            }
        )
    )

    # --------------------------------------------------------
    # Save price
    # --------------------------------------------------------

    if hasattr(
        product,
        "price"
    ):

        product.price = price

        product.save()

    return JsonResponse(
        {
            "success": True,

            "created":
                created,

            "message":
                (
                    "Product saved successfully."
                    if created
                    else
                    "Product updated successfully."
                ),

            "product_id":
                product.id,

            "barcode":
                product.barcode,

            "name":
                product.name,
        }
    )


# ============================================================
# STAFF PRODUCTS
# ============================================================

def staff_products(request):

    products = Product.objects.all().order_by(
        "-id"
    )

    return render(
        request,
        "staff/manage_products.html",
        {
            "products":
                products
        }
    )


# ============================================================
# UPDATE STAFF PRODUCT
# ============================================================

def update_staff_product(
    request,
    product_id
):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        product.name = request.POST.get(
            "name",
            product.name
        )

        product.barcode = request.POST.get(
            "barcode",
            product.barcode
        )

        product.brand = request.POST.get(
            "brand",
            ""
        )

        product.manufacturer = request.POST.get(
            "manufacturer",
            ""
        )

        product.category = request.POST.get(
            "category",
            ""
        )

        product.unit = request.POST.get(
            "unit",
            ""
        )

        product.batch_number = request.POST.get(
            "batch_number",
            ""
        )

        product.description = request.POST.get(
            "description",
            ""
        )

        product.ingredients = request.POST.get(
            "ingredients",
            ""
        )

        quantity_text = request.POST.get(
            "quantity",
            "0"
        )

        try:

            product.quantity = int(
                quantity_text
            )

        except ValueError:

            product.quantity = 0

        manufacture_date = request.POST.get(
            "manufacture_date",
            ""
        )

        expiry_date = request.POST.get(
            "expiry_date",
            ""
        )

        if manufacture_date:

            product.manufacture_date = (
                datetime.strptime(
                    manufacture_date,
                    "%Y-%m-%d"
                ).date()
            )

        else:

            product.manufacture_date = None

        if expiry_date:

            product.expiry_date = (
                datetime.strptime(
                    expiry_date,
                    "%Y-%m-%d"
                ).date()
            )

        else:

            product.expiry_date = None

        if hasattr(
            product,
            "price"
        ):

            price_text = request.POST.get(
                "price",
                "0"
            )

            try:

                product.price = float(
                    price_text
                )

            except ValueError:

                product.price = 0

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

def delete_staff_product(
    request,
    product_id
):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        product.delete()

        messages.success(
            request,
            "Product deleted successfully."
        )

        return redirect(
            "staff_products"
        )

    return render(
        request,
        "staff/delete_product.html",
        {
            "product":
                product
        }
    )


# ============================================================
# EXPIRY DASHBOARD
# ============================================================

def staff_expiry_dashboard(
    request
):

    products = Product.objects.all()

    today = date.today()

    expired = products.filter(
        expiry_date__lt=today
    )

    within_7_days = products.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=7)
    )

    within_15_days = products.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=15)
    )

    within_30_days = products.filter(
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=30)
    )

    safe = products.filter(
        expiry_date__gt=today + timedelta(days=30)
    )

    context = {

        "products":
            products,

        "expired_products":
            expired,

        "within_7_days":
            within_7_days,

        "within_15_days":
            within_15_days,

        "within_30_days":
            within_30_days,

        "safe_products":
            safe,

        "expired_count":
            expired.count(),

        "within_7_count":
            within_7_days.count(),

        "within_15_count":
            within_15_days.count(),

        "within_30_count":
            within_30_days.count(),

        "safe_count":
            safe.count(),
    }

    return render(
        request,
        "staff/expiry_dashboard.html",
        context
    )


# ============================================================
# PRODUCT STATUS
# ============================================================

def staff_product_status(
    request
):

    products = Product.objects.all()

    today = date.today()

    for product in products:

        if not product.expiry_date:

            product.expiry_status = "UNKNOWN"

        else:

            product.expiry_status = (
                calculate_expiry_status(
                    product.expiry_date
                )
            )

    context = {

        "products":
            products,

        "today":
            today,
    }

    return render(
        request,
        "staff/product_status.html",
        context
    )


# ============================================================
# NOTIFICATIONS
# ============================================================

def staff_notifications(
    request
):

    today = date.today()

    products = Product.objects.filter(
        expiry_date__isnull=False
    ).order_by(
        "expiry_date"
    )

    notifications = []

    for product in products:

        status = calculate_expiry_status(
            product.expiry_date
        )

        if status != "SAFE":

            notifications.append(
                {
                    "product":
                        product,

                    "status":
                        status,

                    "expiry_date":
                        product.expiry_date,
                }
            )

    return render(
        request,
        "staff/notifications.html",
        {
            "notifications":
                notifications,

            "today":
                today,
        }
    )


# ============================================================
# STAFF ACCOUNT
# ============================================================

def staff_account(
    request
):

    return render(
        request,
        "staff/account.html",
        {
            "user":
                request.user
        }
    )