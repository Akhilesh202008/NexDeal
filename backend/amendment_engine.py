from functools import lru_cache
from copy import deepcopy


from pathlib import Path
from datetime import date
from decimal import Decimal, InvalidOperation
import re

from category_loader import load_categories


# ==========================================
# NEXDEAL - AMENDMENT ENGINE
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
AMENDMENT_DIR = BASE_DIR / "data" / "playbook" / "amendments"


FIELD_MAP = {
    "target price": "target",
    "walk-away price": "walkaway",
    "walkaway price": "walkaway",
    "approval limit": "approval_limit",
    "negotiation rounds": "rounds",
    "concession exponent": "beta",
    "gst rate": "gst",
}

CATEGORY_ALIASES = {
    "courier services": "courier",
    "cleaning services": "cleaning",
    "training workshops": "training",
}


# ==========================================
# CATEGORY NORMALIZATION
# ==========================================

def normalize_category(name):
    name = str(name).strip().lower()
    name = re.sub(r"\s+", " ", name)

    return CATEGORY_ALIASES.get(
        name,
        name.replace(" ", "-")
    )


# ==========================================
# EXTRACT MARKDOWN FIELD
# ==========================================

def extract_field(content, field):
    pattern = (
        rf"^\s*(?:-\s*)?"
        rf"\*\*{re.escape(field)}:\*\*\s*(.+?)\s*$"
    )

    match = re.search(
        pattern,
        content,
        flags=re.MULTILINE | re.IGNORECASE
    )

    return match.group(1).strip() if match else None


# ==========================================
# PARSE NUMERIC VALUE
# ==========================================

def parse_numeric_value(value, field_name):
    value = str(value).strip()

    match = re.fullmatch(
        r"(?:₹\s*)?"
        r"([0-9][0-9,]*(?:\.[0-9]+)?)"
        r"\s*(%)?",
        value
    )

    if not match:
        raise ValueError(
            f"Invalid amendment value: {value}"
        )

    try:
        number = Decimal(
            match.group(1).replace(",", "")
        )
    except InvalidOperation as exc:
        raise ValueError(
            f"Invalid numeric value: {value}"
        ) from exc

    if not number.is_finite() or number < 0:
        raise ValueError(
            f"Invalid amendment value: {value}"
        )

    if match.group(2) and field_name != "gst":
        raise ValueError(
            f"Unexpected percentage for {field_name}"
        )

    if field_name == "rounds":
        if number < 1 or number != number.to_integral_value():
            raise ValueError(
                "Negotiation rounds must be a positive integer"
            )

    if field_name == "beta" and number <= 0:
        raise ValueError(
            "Concession exponent must be positive"
        )

    return number


# ==========================================
# PARSE AMENDMENT CHANGE
# ==========================================

def parse_change(change_text):
    pattern = (
        r"^the\s+(.+?)\s+for\s+(.+?)"
        r"\s+is\s+now\s+"
        r"(.+?)\s*\.?$"
    )

    match = re.fullmatch(
        pattern,
        change_text.strip(),
        flags=re.IGNORECASE
    )

    if not match:
        raise ValueError(
            f"Unrecognized amendment: {change_text}"
        )

    field_name = match.group(1).strip().lower()
    category = normalize_category(match.group(2))
    raw_value = match.group(3).strip()

    if field_name not in FIELD_MAP:
        raise ValueError(
            f"Unknown amendment field: {field_name}"
        )

    field = FIELD_MAP[field_name]

    value = parse_numeric_value(
        raw_value,
        field
    )

    return category, field, value


# ==========================================
# LOAD OFFICIAL AMENDMENTS
# ==========================================

@lru_cache(maxsize=1)
def _cached_load_amendments():
    if not AMENDMENT_DIR.is_dir():
        raise FileNotFoundError(
            f"Amendment folder missing: {AMENDMENT_DIR}"
        )

    amendments = []

    for file in sorted(AMENDMENT_DIR.glob("*.md")):
        content = file.read_text(
            encoding="utf-8-sig"
        )

        effective_text = extract_field(
            content,
            "Effective from"
        )

        change_text = extract_field(
            content,
            "Change"
        )

        if not effective_text or not change_text:
            raise ValueError(
                f"Missing amendment fields: {file.name}"
            )

        try:
            effective_date = date.fromisoformat(
                effective_text
            )
        except ValueError as exc:
            raise ValueError(
                f"Invalid effective date in {file.name}"
            ) from exc

        try:
            category, field, value = parse_change(
                change_text
            )
        except ValueError as exc:
            raise ValueError(
                f"{file.name}: {exc}"
            ) from exc

        amendments.append({
            "id": file.stem,
            "effective_date": effective_date,
            "category": category,
            "field": field,
            "value": value,
            "description": change_text,
        })

    return sorted(
        amendments,
        key=lambda item: (
            item["effective_date"],
            item["id"]
        )
    )


# ==========================================
# APPLY DATE-SPECIFIC AMENDMENTS
# ==========================================

def get_category_rules(category, thread_date):
    categories = load_categories()
    category = normalize_category(category)

    if category not in categories:
        raise ValueError(
            f"Unknown category: {category}"
        )

    if not thread_date:
        raise ValueError(
            "Thread date is required"
        )

    try:
        cutoff = date.fromisoformat(
            str(thread_date)[:10]
        )
    except ValueError as exc:
        raise ValueError(
            f"Invalid thread date: {thread_date}"
        ) from exc

    rules = categories[category].copy()

    for amendment in load_amendments():

        if amendment["effective_date"] > cutoff:
            continue

        if amendment["category"] != category:
            continue

        # Preserve exact decimal precision.
        rules[amendment["field"]] = amendment["value"]

    return rules


# ==========================================
# LOCAL TESTS
# ==========================================



def load_amendments():
    return deepcopy(_cached_load_amendments())


if __name__ == "__main__":

    amendments = load_amendments()

    print("=" * 50)
    print("NEXDEAL - AMENDMENT ENGINE")
    print("=" * 50)

    print("Amendments loaded:", len(amendments))

    for amendment in amendments:
        print(
            amendment["id"],
            "|",
            amendment["effective_date"],
            "|",
            amendment["category"],
            "|",
            amendment["field"],
            "=",
            amendment["value"]
        )

    print("\nDATE-SPECIFIC RULE TESTS")
    print("-" * 50)

    tests = [
        ("courier", "2026-09-21", "walkaway"),
        ("courier", "2026-09-22", "walkaway"),
        ("headsets", "2026-11-09", "approval_limit"),
        ("led-lighting", "2026-12-04", "walkaway"),
        ("led-lighting", "2026-12-05", "walkaway"),
        ("monitors", "2026-12-14", "approval_limit"),
    ]

    for category, day, field in tests:
        rules = get_category_rules(
            category,
            day
        )

        print(
            f"{category} | {day} | "
            f"{field} = {rules[field]}"
        )

    print("\nAmendment engine completed successfully.")
