# ============================================================
# STAFF / VIEWS.PY
# EXPIRYGUARD
# ============================================================

import re
import cv2
import numpy as np
import pytesseract

from datetime import date, datetime, timedelta
from PIL import Image

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Product


# ============================================================
# TESSERACT CONFIGURATION
# ============================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# ============================================================
# COMMON LOGIN CHECK
# ============================================================

def staff_login_required(request):

    if not request.user.is_authenticated:
        return redirect("staff_login")

    return None


# ============================================================
# ============================================================
# OCR SECTION
# ============================================================
# ============================================================


# ============================================================
# NORMALIZE OCR TEXT
# ============================================================

def normalize_ocr_text(text):

    if not text:
        return ""

    text = str(text)

    text = text.replace("\r", "\n")

    # Remove null characters
    text = text.replace("\x00", "")

    # Normalize spaces
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    # Normalize blank lines
    text = re.sub(
        r"\n+",
        "\n",
        text
    )

    return text.strip()


# ============================================================
# CORRECT COMMON OCR LETTER ERRORS
# ============================================================

def correct_ocr_label(text):

    if not text:
        return ""

    text = text.upper().strip()

    # Common OCR mistakes
    replacements = {

        "MFO": "MFG",
        "MFG.": "MFG",
        "M.F.G": "MFG",
        "M F G": "MFG",

        "EXF": "EXP",
        "EYP": "EXP",
        "E.X.P": "EXP",
        "E X P": "EXP",
        "EXP.": "EXP",

        "8ATCH": "BATCH",
        "B4TCH": "BATCH",
        "B4TCH": "BATCH",
        "BATGH": "BATCH",
        "BATCH.": "BATCH",

        "MANUFACTURED": "MFG",
        "MANUFACTURING": "MFG",
        "MANUFACTURE": "MFG",

        "USEBY": "USE BY",
        "USE-BY": "USE BY",

    }

    for old, new in replacements.items():

        text = text.replace(
            old,
            new
        )

    return text


# ============================================================
# PARSE OCR DATE
# ============================================================

def parse_ocr_date(text):

    if not text:
        return None

    text = str(text).upper().strip()

    # OCR character corrections
    replacements = {
        "O": "0",
        "Q": "0",
        "D": "0",
        "I": "1",
        "L": "1",
        "|": "1",
    }

    for old, new in replacements.items():

        text = text.replace(
            old,
            new
        )

    # Remove unwanted characters
    text = re.sub(
        r"[^0-9./-]",
        "",
        text
    )

    patterns = [

        # DD/MM/YYYY
        r"^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$",

        # DD/MM/YY
        r"^(\d{1,2})[./-](\d{1,2})[./-](\d{2})$",

    ]

    for pattern in patterns:

        match = re.match(
            pattern,
            text
        )

        if not match:
            continue

        day = int(
            match.group(1)
        )

        month = int(
            match.group(2)
        )

        year = int(
            match.group(3)
        )

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


# ============================================================
# FIND DATE CANDIDATES
# ============================================================

def find_date_candidates(text):

    candidates = []

    if not text:
        return candidates

    # Normal date formats
    patterns = [

        r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b",

        r"\b\d{1,2}\s*[./-]\s*\d{1,2}\s*[./-]\s*\d{2,4}\b",

    ]

    found = []

    for pattern in patterns:

        found.extend(
            re.findall(
                pattern,
                text
            )
        )

    seen = set()

    for value in found:

        value = value.strip()

        if value in seen:
            continue

        seen.add(value)

        parsed = parse_ocr_date(
            value
        )

        if parsed:

            candidates.append(
                {
                    "text": value,
                    "date": parsed
                }
            )

    return candidates


# ============================================================
# CLEAN BATCH NUMBER
# ============================================================

def clean_batch_number(value):

    if not value:
        return ""

    value = str(value).upper().strip()

    # Remove spaces
    value = re.sub(
        r"\s+",
        "",
        value
    )

    # Remove unwanted characters
    value = re.sub(
        r"[^A-Z0-9./_-]",
        "",
        value
    )

    return value


# ============================================================
# CHECK WHETHER TEXT LOOKS LIKE A DATE
# ============================================================

def looks_like_date(value):

    if not value:
        return False

    return parse_ocr_date(
        value
    ) is not None


# ============================================================
# EXTRACT BATCH NUMBER
# ============================================================

def extract_batch_from_text(text):

    if not text:
        return ""

    text = normalize_ocr_text(
        text
    )

    # Correct OCR labels
    corrected = correct_ocr_label(
        text
    )

    lines = corrected.splitlines()

    patterns = [

        # BATCH: ABC123
        r"\bBATCH\s*(?:NO|NUMBER|N)?"
        r"\s*[:#.\-]?\s*"
        r"([A-Z0-9][A-Z0-9./_-]{2,30})",

        # BATCH ABC123
        r"\bBATCH\s+"
        r"([A-Z0-9][A-Z0-9./_-]{2,30})",

        # LOT: ABC123
        r"\bLOT\s*(?:NO|NUMBER|N)?"
        r"\s*[:#.\-]?\s*"
        r"([A-Z0-9][A-Z0-9./_-]{2,30})",

        # BN: ABC123
        r"\bBN\s*[:#.\-]?\s*"
        r"([A-Z0-9][A-Z0-9./_-]{2,30})",

        # B NO: ABC123
        r"\bB\s*(?:NO|N)"
        r"\s*[:#.\-]?\s*"
        r"([A-Z0-9][A-Z0-9./_-]{2,30})",

    ]

    # First check line by line
    for line in lines:

        line = line.strip()

        if not line:
            continue

        for pattern in patterns:

            matches = re.findall(
                pattern,
                line,
                re.IGNORECASE
            )

            for value in matches:

                value = clean_batch_number(
                    value
                )

                if not value:
                    continue

                if looks_like_date(value):
                    continue

                # Ignore only-number barcode-like values
                if value.isdigit() and len(value) >= 8:
                    continue

                return value

    # Check entire text
    for pattern in patterns:

        matches = re.findall(
            pattern,
            corrected,
            re.IGNORECASE
        )

        for value in matches:

            value = clean_batch_number(
                value
            )

            if not value:
                continue

            if looks_like_date(value):
                continue

            if value.isdigit() and len(value) >= 8:
                continue

            return value

    return ""


# ============================================================
# EXTRACT LABELED DATE
# ============================================================

def extract_labeled_date(
    text,
    label_patterns
):

    if not text:
        return None

    text = normalize_ocr_text(
        text
    )

    # Correct common OCR mistakes
    text = correct_ocr_label(
        text
    )

    # OCR can insert spaces between characters
    text = re.sub(
        r"M\s+F\s+G",
        "MFG",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"E\s+X\s+P",
        "EXP",
        text,
        flags=re.IGNORECASE
    )

    # Date pattern
    date_pattern = (
        r"([0-9OQDIIL]{1,2}"
        r"\s*[./-]\s*"
        r"[0-9OQDIIL]{1,2}"
        r"\s*[./-]\s*"
        r"[0-9OQDIIL]{2,4})"
    )

    for label in label_patterns:

        pattern = (
            label
            + r"\s*"
            r"(?:DATE|DT)?"
            r"\s*[:.#\-]?\s*"
            + date_pattern
        )

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            parsed = parse_ocr_date(
                match.group(1)
            )

            if parsed:
                return parsed

    return None


# ============================================================
# EXTRACT MFG DATE
# ============================================================

def extract_mfg_date(text):

    labels = [

        r"\bMFG\b",

        r"\bMFD\b",

        r"\bMFGD\b",

        r"\bMANUF\b",

        r"\bMANUFACTURED\b",

        r"\bMANUFACTURING\b",

        r"\bMANUFACTURE\b",

    ]

    return extract_labeled_date(
        text,
        labels
    )


# ============================================================
# EXTRACT EXPIRY DATE
# ============================================================

def extract_expiry_date(text):

    labels = [

        r"\bEXP\b",

        r"\bEXPIRY\b",

        r"\bEXPIRES\b",

        r"\bUSE\s*BY\b",

        r"\bBEST\s*BEFORE\b",

    ]

    return extract_labeled_date(
        text,
        labels
    )


# ============================================================
# FALLBACK MFG + EXP DATE
# ============================================================

def fallback_mfg_exp(text):

    candidates = find_date_candidates(
        text
    )

    manufacture_date = None
    expiry_date = None

    if len(candidates) >= 1:

        manufacture_date = (
            candidates[0]["date"]
        )

    if len(candidates) >= 2:

        expiry_date = (
            candidates[-1]["date"]
        )

    return (
        manufacture_date,
        expiry_date
    )


# ============================================================
# EXTRACT MFG + EXP
# ============================================================

def extract_mfg_exp_from_text(text):

    if not text:

        return (
            None,
            None
        )

    text = normalize_ocr_text(
        text
    )

    manufacture_date = extract_mfg_date(
        text
    )

    expiry_date = extract_expiry_date(
        text
    )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    fallback_mfg = None
    fallback_exp = None

    if (
        not manufacture_date
        or not expiry_date
    ):

        fallback_mfg, fallback_exp = (
            fallback_mfg_exp(text)
        )

    if not manufacture_date:

        manufacture_date = fallback_mfg

    if not expiry_date:

        fallback_candidates = find_date_candidates(
            text
        )

        if len(fallback_candidates) >= 2:

            expiry_date = (
                fallback_candidates[-1]["date"]
            )

    return (
        manufacture_date,
        expiry_date
    )


# ============================================================
# EXTRACT PRICE / MRP
# ============================================================

def extract_price_from_text(text):

    if not text:
        return None

    text = normalize_ocr_text(
        text
    )

    patterns = [

        r"\bMRP\s*[:.#-]?\s*"
        r"(?:RS\.?\s*)?"
        r"(\d+(?:\.\d{1,2})?)",

        r"\bRS\.?\s*[:.#-]?\s*"
        r"(\d+(?:\.\d{1,2})?)",

        r"₹\s*"
        r"(\d+(?:\.\d{1,2})?)",

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            try:

                return float(
                    match.group(1)
                )

            except (
                ValueError,
                TypeError
            ):

                pass

    return None


# ============================================================
# PREPARE MANY OCR IMAGES
# ============================================================

def prepare_ocr_images(image):

    images = []

    # PIL -> RGB
    image = image.convert(
        "RGB"
    )

    image_np = np.array(
        image
    )

    image_cv = cv2.cvtColor(
        image_np,
        cv2.COLOR_RGB2BGR
    )

    # --------------------------------------------------------
    # Resize large image
    # --------------------------------------------------------

    height, width = image_cv.shape[:2]

    if width < 1200:

        scale = 1200 / max(
            width,
            1
        )

        if scale > 1:

            image_cv = cv2.resize(
                image_cv,
                None,
                fx=scale,
                fy=scale,
                interpolation=cv2.INTER_CUBIC
            )

    elif width > 1800:

        scale = 1800 / width

        image_cv = cv2.resize(
            image_cv,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_AREA
        )

    # --------------------------------------------------------
    # GRAYSCALE
    # --------------------------------------------------------

    gray = cv2.cvtColor(
        image_cv,
        cv2.COLOR_BGR2GRAY
    )

    images.append(
        ("gray", gray)
    )

    # --------------------------------------------------------
    # UPSCALE
    # --------------------------------------------------------

    enlarged = cv2.resize(
        gray,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    images.append(
        ("enlarged", enlarged)
    )

    # --------------------------------------------------------
    # CLAHE
    # --------------------------------------------------------

    clahe = cv2.createCLAHE(
        clipLimit=3.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(
        enlarged
    )

    images.append(
        ("enhanced", enhanced)
    )

    # --------------------------------------------------------
    # GAUSSIAN BLUR
    # --------------------------------------------------------

    blurred = cv2.GaussianBlur(
        enhanced,
        (3, 3),
        0
    )

    images.append(
        ("blurred", blurred)
    )

    # --------------------------------------------------------
    # OTSU
    # --------------------------------------------------------

    _, otsu = cv2.threshold(
        enhanced,
        0,
        255,
        cv2.THRESH_BINARY +
        cv2.THRESH_OTSU
    )

    images.append(
        ("otsu", otsu)
    )

    # --------------------------------------------------------
    # INVERSE OTSU
    # --------------------------------------------------------

    _, otsu_inv = cv2.threshold(
        enhanced,
        0,
        255,
        cv2.THRESH_BINARY_INV +
        cv2.THRESH_OTSU
    )

    images.append(
        ("otsu_inverse", otsu_inv)
    )

    # --------------------------------------------------------
    # ADAPTIVE
    # --------------------------------------------------------

    adaptive = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        9
    )

    images.append(
        ("adaptive", adaptive)
    )

    # --------------------------------------------------------
    # ADAPTIVE INVERSE
    # --------------------------------------------------------

    adaptive_inv = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        31,
        9
    )

    images.append(
        ("adaptive_inverse", adaptive_inv)
    )

    # --------------------------------------------------------
    # BLACKHAT
    # --------------------------------------------------------
    # Very useful for dark dot-matrix printing
    # --------------------------------------------------------

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (31, 31)
    )

    blackhat = cv2.morphologyEx(
        enhanced,
        cv2.MORPH_BLACKHAT,
        kernel
    )

    _, blackhat_binary = cv2.threshold(
        blackhat,
        0,
        255,
        cv2.THRESH_BINARY +
        cv2.THRESH_OTSU
    )

    images.append(
        ("blackhat", blackhat_binary)
    )

    # --------------------------------------------------------
    # MORPHOLOGY
    # --------------------------------------------------------

    morph_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (2, 2)
    )

    morph = cv2.morphologyEx(
        otsu,
        cv2.MORPH_CLOSE,
        morph_kernel
    )

    images.append(
        ("morphology", morph)
    )

    return images


# ============================================================
# CREATE OCR REGIONS
# ============================================================

def create_ocr_regions(image):

    regions = []

    image = image.convert(
        "RGB"
    )

    image_np = np.array(
        image
    )

    image_cv = cv2.cvtColor(
        image_np,
        cv2.COLOR_RGB2BGR
    )

    height, width = image_cv.shape[:2]

    # --------------------------------------------------------
    # FULL IMAGE
    # --------------------------------------------------------

    regions.append(
        (
            "full",
            image_cv
        )
    )

    # --------------------------------------------------------
    # CENTER REGION
    # --------------------------------------------------------

    x1 = int(
        width * 0.05
    )

    x2 = int(
        width * 0.95
    )

    y1 = int(
        height * 0.10
    )

    y2 = int(
        height * 0.90
    )

    center = image_cv[
        y1:y2,
        x1:x2
    ]

    if center.size > 0:

        regions.append(
            (
                "center",
                center
            )
        )

    # --------------------------------------------------------
    # TOP HALF
    # --------------------------------------------------------

    top = image_cv[
        0:int(height * 0.60),
        :
    ]

    if top.size > 0:

        regions.append(
            (
                "top",
                top
            )
        )

    # --------------------------------------------------------
    # MIDDLE
    # --------------------------------------------------------

    middle = image_cv[
        int(height * 0.20):
        int(height * 0.80),
        :
    ]

    if middle.size > 0:

        regions.append(
            (
                "middle",
                middle
            )
        )

    # --------------------------------------------------------
    # BOTTOM HALF
    # --------------------------------------------------------

    bottom = image_cv[
        int(height * 0.40):,
        :
    ]

    if bottom.size > 0:

        regions.append(
            (
                "bottom",
                bottom
            )
        )

    return regions


# ============================================================
# RUN OCR ON IMAGE
# ============================================================

def perform_advanced_ocr(image):

    all_text = []

    # --------------------------------------------------------
    # OCR REGIONS
    # --------------------------------------------------------

    regions = create_ocr_regions(
        image
    )

    # Limit OCR workload
    # but still use many preprocessing methods
    for region_name, region in regions:

        region_pil = Image.fromarray(
            cv2.cvtColor(
                region,
                cv2.COLOR_BGR2RGB
            )
        )

        processed_images = prepare_ocr_images(
            region_pil
        )

        for image_name, processed in processed_images:

            # Several PSM modes
            for psm in [6, 11, 12]:

                config = (
                    f"--oem 3 --psm {psm}"
                )

                try:

                    text = pytesseract.image_to_string(
                        processed,
                        config=config
                    )

                except Exception as e:

                    print(
                        "OCR error:",
                        e
                    )

                    text = ""

                text = normalize_ocr_text(
                    text
                )

                if text:

                    all_text.append(
                        text
                    )

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    unique_texts = []

    seen = set()

    for text in all_text:

        key = text.upper().strip()

        if key in seen:
            continue

        seen.add(key)

        unique_texts.append(
            text
        )

    return "\n".join(
        unique_texts
    )


# ============================================================
# EXTRACT PRODUCT DETAILS FROM OCR TEXT
# ============================================================

def extract_product_details_from_text(text):

    text = normalize_ocr_text(
        text
    )

    # --------------------------------------------------------
    # BATCH
    # --------------------------------------------------------

    batch_number = extract_batch_from_text(
        text
    )

    # --------------------------------------------------------
    # MFG + EXP
    # --------------------------------------------------------

    manufacture_date, expiry_date = (
        extract_mfg_exp_from_text(
            text
        )
    )

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    price = extract_price_from_text(
        text
    )

    return {

        "batch_number":
            batch_number,

        "manufacture_date":
            (
                manufacture_date.strftime(
                    "%Y-%m-%d"
                )
                if manufacture_date
                else ""
            ),

        "expiry_date":
            (
                expiry_date.strftime(
                    "%Y-%m-%d"
                )
                if expiry_date
                else ""
            ),

        "price":
            price,

        "ocr_text":
            text,

    }


# ============================================================
# OCR IMAGE UPLOAD API
# ============================================================

@require_POST
def extract_product_details_from_image(
    request
):

    check = staff_login_required(
        request
    )

    if check:
        return check

    uploaded_file = request.FILES.get(
        "product_image"
    )

    if not uploaded_file:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Please upload an image."
            },
            status=400
        )

    try:

        image = Image.open(
            uploaded_file
        )

        image.load()

        image = image.convert(
            "RGB"
        )

    except Exception:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Invalid image file."
            },
            status=400
        )

    try:

        ocr_text = perform_advanced_ocr(
            image
        )

        details = (
            extract_product_details_from_text(
                ocr_text
            )
        )

        print("\n")
        print("=" * 70)
        print("EXPIRYGUARD OCR TEXT")
        print("=" * 70)
        print(ocr_text)
        print("=" * 70)
        print(
            "BATCH:",
            details["batch_number"]
        )
        print(
            "MFG:",
            details["manufacture_date"]
        )
        print(
            "EXP:",
            details["expiry_date"]
        )
        print("=" * 70)
        print("\n")

        return JsonResponse(
            {
                "success": True,
                **details,
            }
        )

    except Exception as e:

        print(
            "OCR ERROR:",
            e
        )

        return JsonResponse(
            {
                "success": False,
                "message":
                    "OCR processing failed: "
                    + str(e)
            },
            status=500
        )


# ============================================================
# OCR CAMERA API
# ============================================================

@require_POST
def ocr_camera(request):

    check = staff_login_required(
        request
    )

    if check:
        return check

    uploaded_file = request.FILES.get(
        "image"
    )

    if not uploaded_file:

        uploaded_file = request.FILES.get(
            "product_image"
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

        image = Image.open(
            uploaded_file
        )

        image.load()

        image = image.convert(
            "RGB"
        )

    except Exception:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Unable to read camera image."
            },
            status=400
        )

    try:

        ocr_text = perform_advanced_ocr(
            image
        )

        details = (
            extract_product_details_from_text(
                ocr_text
            )
        )

        print("\n")
        print("=" * 70)
        print("CAMERA OCR")
        print("=" * 70)
        print(ocr_text)
        print("=" * 70)
        print(
            "BATCH:",
            details["batch_number"]
        )
        print(
            "MFG:",
            details["manufacture_date"]
        )
        print(
            "EXP:",
            details["expiry_date"]
        )
        print("=" * 70)
        print("\n")

        return JsonResponse(
            {
                "success": True,
                **details,
            }
        )

    except Exception as e:

        print(
            "CAMERA OCR ERROR:",
            e
        )

        return JsonResponse(
            {
                "success": False,
                "message":
                    "OCR processing failed: "
                    + str(e)
            },
            status=500
        )


# ============================================================
# ============================================================
# STAFF LOGIN
# ============================================================
# ============================================================

def staff_login(request):

    if request.user.is_authenticated:

        return redirect(
            "staff_home"
        )

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

    logout(
        request
    )

    return redirect(
        "staff_login"
    )


# ============================================================
# STAFF HOME
# ============================================================

def staff_home(request):

    check = staff_login_required(
        request
    )

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
        expiry_date__lte=(
            today + timedelta(days=30)
        )
    ).count()

    safe_products = products.filter(
        expiry_date__gt=(
            today + timedelta(days=30)
        )
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

    check = staff_login_required(
        request
    )

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
        expiry_date__lte=(
            today + timedelta(days=30)
        )
    ).count()

    safe_products = products.filter(
        expiry_date__gt=(
            today + timedelta(days=30)
        )
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

    check = staff_login_required(
        request
    )

    if check:
        return check

    return render(
        request,
        "staff/barcode_product.html"
    )


# ============================================================
# BARCODE
# ============================================================
# IMPORTANT:
# Barcode ONLY.
# No database lookup.
# No Open Food Facts.
# ============================================================

def get_product_from_barcode(request):

    check = staff_login_required(
        request
    )

    if check:
        return check

    barcode = request.GET.get(
        "barcode",
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

    return JsonResponse(
        {
            "success": True,
            "barcode": barcode,
            "new_product": True,
            "message":
                "New product barcode detected."
        }
    )


# ============================================================
# EXPIRY STATUS
# ============================================================

def calculate_expiry_status(
    expiry_date
):

    if not expiry_date:

        return "UNKNOWN"

    today = date.today()

    if expiry_date < today:

        return "EXPIRED"

    if expiry_date <= (
        today + timedelta(days=30)
    ):

        return "NEAR EXPIRY"

    return "SAFE"


# ============================================================
# SAVE SCANNED PRODUCT
# ============================================================

@require_POST
def save_scanned_product(
    request
):

    check = staff_login_required(
        request
    )

    if check:
        return check

    barcode = request.POST.get(
        "barcode",
        ""
    ).strip()

    name = request.POST.get(
        "name",
        ""
    ).strip()

    category = request.POST.get(
        "category",
        ""
    ).strip()

    batch_number = request.POST.get(
        "batch_number",
        ""
    ).strip()

    quantity_text = request.POST.get(
        "quantity",
        "0"
    ).strip()

    unit = request.POST.get(
        "unit",
        ""
    ).strip()

    manufacture_date_text = request.POST.get(
        "manufacture_date",
        ""
    ).strip()

    expiry_date_text = request.POST.get(
        "expiry_date",
        ""
    ).strip()

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

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

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Product name is required."
            },
            status=400
        )

    if not expiry_date_text:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Expiry date is required. "
                    "Please scan the packet using OCR."
            },
            status=400
        )

    # --------------------------------------------------------
    # DUPLICATE BARCODE
    # --------------------------------------------------------

    if Product.objects.filter(
        barcode=barcode
    ).exists():

        return JsonResponse(
            {
                "success": False,
                "message":
                    "A product with this barcode "
                    "already exists in the database."
            },
            status=400
        )

    # --------------------------------------------------------
    # QUANTITY
    # --------------------------------------------------------

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
    # MANUFACTURE DATE
    # --------------------------------------------------------

    manufacture_date = None

    if manufacture_date_text:

        try:

            manufacture_date = (
                datetime.strptime(
                    manufacture_date_text,
                    "%Y-%m-%d"
                ).date()
            )

        except ValueError:

            manufacture_date = (
                parse_ocr_date(
                    manufacture_date_text
                )
            )

    # --------------------------------------------------------
    # EXPIRY DATE
    # --------------------------------------------------------

    expiry_date = None

    if expiry_date_text:

        try:

            expiry_date = (
                datetime.strptime(
                    expiry_date_text,
                    "%Y-%m-%d"
                ).date()
            )

        except ValueError:

            expiry_date = (
                parse_ocr_date(
                    expiry_date_text
                )
            )

    if expiry_date is None:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Invalid expiry date."
            },
            status=400
        )

    # --------------------------------------------------------
    # CREATE NEW PRODUCT
    # --------------------------------------------------------

    try:

        product = Product.objects.create(

            name=name,

            barcode=barcode,

            batch_number=batch_number,

            manufacture_date=(
                manufacture_date
            ),

            expiry_date=(
                expiry_date
            ),

            category=category,

            quantity=quantity,

            unit=unit

        )

    except Exception as e:

        return JsonResponse(
            {
                "success": False,
                "message":
                    "Unable to save product: "
                    + str(e)
            },
            status=500
        )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status = calculate_expiry_status(
        expiry_date
    )

    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    return JsonResponse(
        {
            "success": True,

            "created": True,

            "message":
                "New product saved successfully.",

            "product_id":
                product.id,

            "status":
                status,

            "product":
                {
                    "name":
                        product.name,

                    "barcode":
                        product.barcode,

                    "category":
                        product.category or "",

                    "quantity":
                        product.quantity,

                    "unit":
                        product.unit or "",

                    "batch_number":
                        product.batch_number or "",

                    "manufacture_date":
                        (
                            product.manufacture_date.strftime(
                                "%d/%m/%Y"
                            )
                            if product.manufacture_date
                            else ""
                        ),

                    "expiry_date":
                        (
                            product.expiry_date.strftime(
                                "%d/%m/%Y"
                            )
                            if product.expiry_date
                            else ""
                        ),

                    "status":
                        status,
                }
        }
    )


# ============================================================
# STAFF PRODUCTS
# ============================================================

def staff_products(request):

    check = staff_login_required(
        request
    )

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
# UPDATE STAFF PRODUCT
# ============================================================

def update_staff_product(
    request,
    product_id
):

    check = staff_login_required(
        request
    )

    if check:
        return check

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

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
            product.category
        ).strip()

        product.batch_number = request.POST.get(
            "batch_number",
            product.batch_number
        ).strip()

        product.unit = request.POST.get(
            "unit",
            product.unit
        ).strip()

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

        manufacture_date = request.POST.get(
            "manufacture_date"
        )

        expiry_date = request.POST.get(
            "expiry_date"
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

    check = staff_login_required(
        request
    )

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

    check = staff_login_required(
        request
    )

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

    check = staff_login_required(
        request
    )

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

    check = staff_login_required(
        request
    )

    if check:
        return check

    products = Product.objects.all()

    today = date.today()

    notifications = []

    expired_count = 0

    near_expiry_count = 0

    safe_count = 0

    for product in products:

        if not product.expiry_date:

            notifications.append(
                {
                    "type":
                        "unknown",

                    "title":
                        "Expiry Date Missing",

                    "message":
                        (
                            f"{product.name} "
                            "does not have an expiry date."
                        ),

                    "product":
                        product,
                }
            )

            continue

        if product.expiry_date < today:

            expired_count += 1

            notifications.append(
                {
                    "type":
                        "expired",

                    "title":
                        "Product Expired",

                    "message":
                        (
                            f"{product.name} "
                            "has expired."
                        ),

                    "product":
                        product,
                }
            )

        elif product.expiry_date <= (
            today + timedelta(days=30)
        ):

            near_expiry_count += 1

            days_left = (
                product.expiry_date - today
            ).days

            notifications.append(
                {
                    "type":
                        "warning",

                    "title":
                        "Product Near Expiry",

                    "message":
                        (
                            f"{product.name} "
                            f"will expire in "
                            f"{days_left} day(s)."
                        ),

                    "product":
                        product,
                }
            )

        else:

            safe_count += 1

    context = {

        "notifications":
            notifications,

        "today":
            today,

        "expired_count":
            expired_count,

        "near_expiry_count":
            near_expiry_count,

        "safe_count":
            safe_count,

    }

    return render(
        request,
        "staff/notifications.html",
        context
    )


# ============================================================
# STAFF ACCOUNT
# ============================================================

def staff_account(request):

    check = staff_login_required(
        request
    )

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