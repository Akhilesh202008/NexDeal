
import csv
import re
from pathlib import Path
from decimal import Decimal, InvalidOperation


# ==========================================
# NEXDEAL - EMAIL PARSER
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "threads.csv"

NUMBER = r"\d[\d,]*(?:\.\d+)?"

CURRENCY = (
    r"(?:INR|Rs\.?|₹|USD|EUR|GBP|"
    r"SGD|JPY|AUD|CAD|CHF|CNY|AED|S\$|\$|€|£)"
)

CURRENCY_MAP = {
    "INR": "INR",
    "RS": "INR",
    "RS.": "INR",
    "₹": "INR",
    "USD": "USD",
    "$": "USD",
    "EUR": "EUR",
    "€": "EUR",
    "GBP": "GBP",
    "£": "GBP",
    "SGD": "SGD",
    "S$": "SGD",
    "JPY": "JPY",
    "AUD": "AUD",
    "CAD": "CAD",
    "CHF": "CHF",
    "CNY": "CNY",
    "AED": "AED",
}

SUPPORTED_CURRENCIES = {
    "INR", "USD", "EUR", "GBP"
}

NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2,
    "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8,
    "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90
}

SCALES = {
    "hundred": 100,
    "thousand": 1000,
    "lakh": 100000,
    "lakhs": 100000,
    "million": 1000000,
    "crore": 10000000,
    "crores": 10000000
}

SUFFIXES = {
    "k": Decimal("1000"),
    "thousand": Decimal("1000"),
    "lakh": Decimal("100000"),
    "lakhs": Decimal("100000"),
    "million": Decimal("1000000"),
    "crore": Decimal("10000000"),
    "crores": Decimal("10000000")
}

BILLING_PERIODS = {
    "crm-licenses": "year",
    "design-software": "year",
    "cloud-servers": "year",
    "cleaning": "month",
    "security-guards": "month"
}

CATEGORY_ALIASES = {
    "cleaning-services": "cleaning",
    "courier-services": "courier",
    "training-workshops": "training"
}

WORD_PATTERN = "|".join(
    list(NUMBER_WORDS) + list(SCALES)
)

MONEY_PATTERN = re.compile(
    rf"(?<!\w)({CURRENCY})\s*"
    rf"({NUMBER})"
    rf"(?:\s*(k|thousand|lakhs?|million|crores?)\b)?",
    re.IGNORECASE
)

WORD_MONEY_PATTERN = re.compile(
    rf"(?<!\w)({CURRENCY})\s+"
    rf"((?:{WORD_PATTERN})\b"
    rf"(?:(?:[\s-]+)(?:{WORD_PATTERN}|and)\b)*)",
    re.IGNORECASE
)

MESSAGE_HEADER = re.compile(
    r"\[(?:Earlier|Latest)\s+message[^\]]*\]",
    re.IGNORECASE
)

PERCENT = r"(\d+(?:\.\d+)?)\s*(?:%|percent\b)"

DISCOUNT_PATTERN = re.compile(
    PERCENT +
    r"\s*off\s+for\s+orders\s+of\s+"
    r"(\d[\d,]*)\s+[\w-]+\s+or\s+more",
    re.IGNORECASE
)


# ==========================================
# NUMBER CONVERSION
# ==========================================

def words_to_number(text):
    total = 0
    current = 0

    words = text.lower().replace("-", " ").split()

    for word in words:

        if word == "and":
            continue

        if word in NUMBER_WORDS:
            current += NUMBER_WORDS[word]

        elif word == "hundred":
            current = (current or 1) * 100

        elif word in SCALES:
            total += (current or 1) * SCALES[word]
            current = 0

        else:
            raise ValueError("Unknown number word")

    return Decimal(total + current)


def normalize_category(category):
    key = str(category or "").strip().lower()
    key = key.replace(" ", "-")
    return CATEGORY_ALIASES.get(key, key)


# ==========================================
# LATEST SUPPLIER MESSAGE
# ==========================================

def latest_supplier_message(text):
    text = text or ""

    matches = list(re.finditer(
        r"\[Latest\s+message[^\]]*\]",
        text,
        re.IGNORECASE
    ))

    if matches:
        return text[matches[-1].end():].strip()

    return text.strip()


# ==========================================
# MONEY EXTRACTION
# ==========================================

def parse_money(text):
    text = text or ""
    results = []

    for match in MONEY_PATTERN.finditer(text):

        currency = CURRENCY_MAP.get(
            match.group(1).upper()
        )

        try:
            amount = Decimal(
                match.group(2).replace(",", "")
            )

            suffix = match.group(3)

            if suffix:
                amount *= SUFFIXES[suffix.lower()]

        except (InvalidOperation, KeyError):
            continue

        if currency is None or not amount.is_finite():
            continue

        results.append({
            "amount": amount,
            "currency": currency,
            "position": match.end(),
            "start": match.start(),
        })

    for match in WORD_MONEY_PATTERN.finditer(text):

        currency = CURRENCY_MAP.get(
            match.group(1).upper()
        )

        try:
            amount = words_to_number(match.group(2))
        except ValueError:
            continue

        if currency is None:
            continue

        results.append({
            "amount": amount,
            "currency": currency,
            "position": match.end(),
            "start": match.start(),
        })


    # Support written amounts followed by currency.
    suffix_pattern = re.compile(
        rf"\b((?:{WORD_PATTERN})\b"
        rf"(?:(?:[\s-]+)(?:{WORD_PATTERN}|and)\b)*)"
        rf"\s+(rupees?|dollars?|euros?|pounds?)\b",
        re.IGNORECASE
    )

    suffix_currencies = {
        "rupee": "INR",
        "rupees": "INR",
        "dollar": "USD",
        "dollars": "USD",
        "euro": "EUR",
        "euros": "EUR",
        "pound": "GBP",
        "pounds": "GBP",
    }

    for match in suffix_pattern.finditer(text):

        if any(
            match.start() < item["position"]
            and match.end() > item["start"]
            for item in results
        ):
            continue

        try:
            amount = words_to_number(match.group(1))
            currency = suffix_currencies[
                match.group(2).lower()
            ]
        except (ValueError, KeyError):
            continue

        results.append({
            "amount": amount,
            "currency": currency,
            "position": match.end(),
            "start": match.start(),
        })

    return sorted(
        results,
        key=lambda item: item["start"]
    )


# ==========================================
# PRICE SELECTION
# ==========================================

def extract_price(text, quantity=None):
    text = text or ""
    offers = parse_money(text)

    if not offers:
        return None


    # Select the price matching the order quantity.
    for first, second in zip(offers, offers[1:]):

        between = text[
            first["position"]:second["start"]
        ]

        after = text[
            second["position"]:
            second["position"] + 150
        ]

        threshold = re.search(
            r"\bfor\s+orders\s+of\s+up\s+to\s+"
            r"(\d[\d,]*)\s+[\w-]+",
            between,
            re.IGNORECASE
        )

        larger = re.search(
            r"\bfor\s+larger\s+orders\b",
            after,
            re.IGNORECASE
        )

        if threshold and larger:

            if quantity is None:
                return None

            limit = int(
                threshold.group(1).replace(",", "")
            )

            if int(quantity) <= limit:
                return first

            return second

    # Conditional price ranges.
    for first, second in zip(offers, offers[1:]):

        before = text[
            max(0, first["start"] - 30):
            first["start"]
        ]

        between = text[
            first["position"]:second["start"]
        ]

        if (
            re.search(r"\bbetween\s*$", before, re.I)
            and re.fullmatch(r"\s*and\s*", between, re.I)
            and first["currency"] == second["currency"]
        ):
            return max(
                (first, second),
                key=lambda item: item["amount"]
            )

    # Explicit corrections.
    correction = re.search(
        r"\b(?:should\s+read|"
        r"corrected?\s+(?:price|to))\b",
        text,
        re.IGNORECASE
    )

    if correction:
        following = [
            offer for offer in offers
            if offer["start"] >= correction.end()
        ]

        if following:
            return following[0]

    # Revised or final offers.
    revised = re.search(
        r"\b(?:revised|updated|final|new)\s+"
        r"(?:unit\s+)?(?:offer|price|quote)\s+"
        r"(?:is|of|at|:)\s*",
        text,
        re.IGNORECASE
    )

    if revised:
        following = [
            offer for offer in offers
            if offer["start"] >= revised.end()
        ]

        if following:
            return following[0]

    # Price A, not price B.
    for offer in offers:

        following_text = text[
            offer["position"]:
            offer["position"] + 40
        ]

        if re.match(
            rf"\s*,?\s*(?:rather\s+than|not)"
            rf"\s+{CURRENCY}",
            following_text,
            re.IGNORECASE
        ):
            return offer

    # Explicit unit price.
    unit = re.search(
        r"\b(?:unit\s+price|price\s+per\s+"
        r"(?:unit|phone|laptop|piece))"
        r"\s*(?:is|was|of|at|:)?\s*",
        text,
        re.IGNORECASE
    )

    if unit:
        candidates = [
            offer for offer in offers
            if offer["start"] >= unit.end()
        ]

        if candidates:
            return candidates[0]

    return offers[-1]


# ==========================================
# UNIT NORMALIZATION
# ==========================================

def extract_unit_divisor(
    text,
    price_position,
    category=None
):
    category = normalize_category(category)

    context = (text or "")[
        price_position:price_position + 120
    ]

    if re.search(
        r"\bper\s+dozen\b",
        context,
        re.I
    ):
        return Decimal("12"), "dozen"

    bulk = re.search('\\bper\\s+([1-9][0-9,]*)\\s+[a-zA-Z-]+\\b', context, re.I)
    if bulk:
        return Decimal(bulk.group(1).replace(',', '')), 'bulk'

    pack = re.search(
        r"\bper\s+pack\s+of\s+(\d+)\b",
        context,
        re.I
    )

    if pack:
        count = int(pack.group(1))

        if count > 0:
            return Decimal(count), "pack"

    if category == "led-lighting":

        if re.search(
            r"\bper\s+pack\b",
            context,
            re.I
        ):
            return Decimal("4"), "pack"

    if category == "printer-paper":

        if re.search(
            r"\bper\s+ream\b",
            context,
            re.I
        ):
            return Decimal("0.1"), "ream"

    if re.search(
        r"\bper\s+box\b",
        context,
        re.I
    ):
        return Decimal("1"), "box"

    return Decimal("1"), "single"


# ==========================================
# BILLING PERIOD NORMALIZATION
# ==========================================

def extract_billing_period(text):

    monthly = bool(re.search(
        r"\b(?:per\s+month|monthly|"
        r"each\s+month|a\s+month)\b|"
        r"/\s*(?:month|mo)\b",
        text,
        re.I
    ))

    yearly = bool(re.search(
        r"\b(?:per\s+year|yearly|annually|"
        r"annual|per\s+annum|each\s+year|"
        r"a\s+year)\b|/\s*(?:year|yr)\b",
        text,
        re.I
    ))

    if monthly and yearly:
        return "ambiguous"

    if monthly:
        return "month"

    if yearly:
        return "year"

    return None


def normalize_billing(
    price,
    source,
    category
):
    category = normalize_category(category)

    expected = BILLING_PERIODS.get(category)
    actual = extract_billing_period(source)

    if expected is None:
        return price, actual, None

    if actual is None:
        return None, None, "Missing billing period"

    if actual == "ambiguous":
        return None, actual, "Ambiguous billing period"

    if expected == "year" and actual == "month":
        price *= Decimal("12")

    elif expected == "month" and actual == "year":
        price /= Decimal("12")

    return price, expected, None


# ==========================================
# FREE-UNIT OFFERS
# ==========================================

def normalize_free_units(price, text):

    match = re.search(
        r"\b(\d+)\s+free\s+[\w-]+\s+"
        r"for\s+every\s+(\d+)\s+"
        r"(?:you\s+)?pay\s+for\b",
        text,
        re.I
    )

    if not match:
        return price

    free = Decimal(match.group(1))
    paid = Decimal(match.group(2))

    if paid <= 0:
        return price

    return price * paid / (paid + free)


# ==========================================
# EARLIER SUPPLIER QUOTES
# ==========================================

def get_earlier_supplier_quote(message, quantity=None):
    message = message or ""

    matches = list(
        MESSAGE_HEADER.finditer(message)
    )

    if not matches:
        return None

    supplier_quotes = []

    for index, match in enumerate(matches):

        header = match.group()
        start = match.end()

        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(message)
        )

        if "latest message" in header.lower():
            break

        if "acme procurement" in header.lower():
            continue

        body = message[start:end]
        offer = extract_price(body, quantity=quantity)

        if offer is not None:
            offer["source"] = body
            supplier_quotes.append(offer)

    return (
        supplier_quotes[-1]
        if supplier_quotes
        else None
    )


# ==========================================
# DISCOUNT EXTRACTION
# ==========================================

def extract_discount(latest, full_message, quantity=None):

    discount_percent = None
    discount_threshold = None
    earlier_offer = None
    review_reasons = []

    quantity_discount = DISCOUNT_PATTERN.search(
        latest
    )

    list_discount = re.search(
        PERCENT +
        r"\s*(?:discount\s+on|off)\s+"
        r"(?:our\s+|the\s+)?list\s+price",
        latest,
        re.I
    )

    previous_discount = re.search(
        PERCENT +
        r"\s*(?:off|discount\s+on)\s+"
        r"our\s+previous\s+quote",
        latest,
        re.I
    )

    if quantity_discount:

        discount_percent = Decimal(
            quantity_discount.group(1)
        )

        discount_threshold = int(
            quantity_discount.group(2).replace(",", "")
        )

    elif list_discount:

        discount_percent = Decimal(
            list_discount.group(1)
        )

        threshold_match = re.search(r'([0-9][0-9,]*) +or +more', latest, re.IGNORECASE)
        discount_threshold = int(threshold_match.group(1).replace(',', '')) if threshold_match else 0

    elif previous_discount:

        earlier_offer = get_earlier_supplier_quote(
            full_message, quantity=quantity
        )

        if earlier_offer:

            discount_percent = Decimal(
                previous_discount.group(1)
            )

            discount_threshold = 0

        else:
            review_reasons.append(
                "Previous supplier quote unavailable"
            )

    elif re.search(
        PERCENT + r"\s*(?:off|discount)",
        latest,
        re.I
    ):
        review_reasons.append(
            "Unresolved discount condition"
        )

    if discount_percent is not None:

        if not (
            Decimal("0")
            <= discount_percent
            <= Decimal("100")
        ):
            review_reasons.append(
                "Invalid discount percentage"
            )

    return (
        discount_percent,
        discount_threshold,
        earlier_offer,
        review_reasons
    )


# ==========================================
# MAIN EMAIL EXTRACTION
# ==========================================

def extract_email_data(message, category=None, quantity=None):

    message = message or ""
    latest = latest_supplier_message(message)

    (
        discount_percent,
        discount_threshold,
        earlier_offer,
        review_reasons
    ) = extract_discount(latest, message, quantity=quantity)

    offer = extract_price(latest, quantity=quantity)
    offer_source = latest

    if earlier_offer is not None:

        offer = earlier_offer
        offer_source = earlier_offer.get(
            "source", ""
        )

    gst_inclusive = bool(re.search(
        r"\b(?:GST\s+included|including\s+GST|"
        r"inclusive\s+of\s+GST|incl\.?\s+GST)\b",
        offer_source,
        re.I
    ))

    is_total_price = bool(re.search(
        r"\b(?:in\s+total|total\s+for\s+all|"
        r"total\s+price|lump\s+sum)\b",
        offer_source,
        re.I
    ))

    price = None
    currency = None
    unit = None
    billing_period = None

    if offer is None:

        review_reasons.append(
            "No recognizable monetary offer"
        )

    elif offer["currency"] not in SUPPORTED_CURRENCIES:

        review_reasons.append(
            "Unsupported currency"
        )

    else:

        currency = offer["currency"]

        divisor, unit = extract_unit_divisor(
            offer_source,
            offer["position"],
            category
        )

        price = offer["amount"] / divisor

        price = normalize_free_units(
            price,
            offer_source
        )

        (
            price,
            billing_period,
            billing_error
        ) = normalize_billing(
            price,
            offer_source,
            category
        )

        if billing_error:
            review_reasons.append(billing_error)

    return {
        "price": price,
        "currency": currency,
        "unit": unit,
        "billing_period": billing_period,
        "gst_inclusive": gst_inclusive,
        "is_total_price": is_total_price,
        "latest_message": latest,
        "email_text": message,
        "discount_percent": discount_percent,
        "discount_threshold": discount_threshold,
        "needs_review": bool(review_reasons),
        "review_reason": ", ".join(review_reasons),
    }


# ==========================================
# LOCAL DATASET TEST
# ==========================================

def main():

    if not CSV_PATH.exists():
        print("CSV not found:", CSV_PATH)
        return

    with CSV_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        rows = list(csv.DictReader(file))

    print("=" * 50)
    print("NEXDEAL - EMAIL PARSER")
    print("=" * 50)
    print("Total threads:", len(rows))

    for row in rows[:10]:

        result = extract_email_data(
            row["supplier_message"],
            category=row["category"]
        )

        print("\nThread:", row["thread_id"])

        for key, value in result.items():

            if key not in (
                "email_text",
                "latest_message"
            ):
                print(key, ":", value)


if __name__ == "__main__":
    main()
