from functools import lru_cache
from copy import deepcopy


from pathlib import Path
from decimal import Decimal
import re


# ==========================================
# NEXDEAL - SUPPLIER LOADER
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

SUPPLIER_DIR = (
    BASE_DIR / "data" / "playbook" / "suppliers"
)


# ==========================================
# EXTRACT NUMERIC VALUES
# ==========================================

def extract_number(text):
    """Extract a numeric value using Decimal."""

    if text is None or str(text).strip() == "":
        return None

    match = re.search(
        r"\d[\d,]*(?:\.\d+)?",
        str(text)
    )

    if not match:
        return None

    return Decimal(
        match.group().replace(",", "")
    )


# ==========================================
# EXTRACT MARKDOWN FIELDS
# ==========================================

def extract_field(content, field):
    """Extract a field from a supplier Markdown profile."""

    pattern = (
        rf"^\s*(?:-\s*)?"
        rf"\*\*{re.escape(field)}:\*\*\s*(.*?)\s*$"
    )

    match = re.search(
        pattern,
        content,
        flags=re.MULTILINE | re.IGNORECASE
    )

    return match.group(1).strip() if match else None


# ==========================================
# NORMALIZE SUPPLIER STATUS
# ==========================================

def normalize_status(status_text):
    """Convert supplier status to a standard value."""

    if not status_text:
        return "UNKNOWN"

    status = str(status_text).upper().strip()

    if "BLACKLISTED" in status:
        return "BLACKLISTED"

    if "PROBATION" in status:
        return "PROBATION"

    if "APPROVED" in status:
        return "APPROVED"

    if "ACTIVE" in status:
        return "ACTIVE"

    return "UNKNOWN"


# ==========================================
# LOAD SUPPLIER PROFILES
# ==========================================

@lru_cache(maxsize=1)
def _cached_load_suppliers():
    """Load all supplier profiles from the playbook."""

    if not SUPPLIER_DIR.is_dir():
        raise FileNotFoundError(
            f"Supplier folder not found: {SUPPLIER_DIR}"
        )

    files = sorted(
        SUPPLIER_DIR.glob("*.md")
    )

    if not files:
        raise FileNotFoundError(
            f"No supplier profiles found: {SUPPLIER_DIR}"
        )

    suppliers = {}

    for file in files:

        content = file.read_text(
            encoding="utf-8-sig"
        )

        # Extract supplier name.
        name_match = re.search(
            r"^#\s*Supplier:\s*(.+?)\s*$",
            content,
            flags=re.MULTILINE | re.IGNORECASE
        )

        name = (
            name_match.group(1).strip()
            if name_match
            else file.stem
        )

        # Extract supplier information.
        status_text = extract_field(
            content, "Status"
        )

        contract = extract_field(
            content, "Contract"
        )

        notes = extract_field(
            content, "Notes"
        )

        status = normalize_status(
            status_text
        )

        # Preserve the existing return structure.
        suppliers[name.casefold()] = {
            "name": name,
            "status": status,
            "status_details": status_text,
            "contract": contract,
            "notes": notes,
            "raw_profile": content,
        }

    return suppliers


# ==========================================
# LOCAL TESTS
# ==========================================



def load_suppliers():
    return deepcopy(_cached_load_suppliers())


if __name__ == "__main__":

    suppliers = load_suppliers()

    print("=" * 50)
    print("NEXDEAL - SUPPLIER LOADER")
    print("=" * 50)

    print("Suppliers loaded:", len(suppliers))

    test_suppliers = [
        "banyan guarding",
        "indus paper mills",
        "arvind office supplies",
    ]

    for name in test_suppliers:

        supplier = suppliers.get(
            name.casefold()
        )

        print("\nSupplier:", name.title())

        if supplier:
            print(
                "Status:",
                supplier["status"]
            )

            print(
                "Details:",
                supplier["status_details"]
            )

            print(
                "Contract:",
                supplier["contract"]
            )

            print(
                "Notes:",
                supplier["notes"]
            )

        else:
            print("Supplier not found")

    print("\nSupplier loader completed successfully.")
