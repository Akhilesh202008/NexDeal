
import re
from decimal import Decimal
from supplier_loader import load_suppliers

# ==========================================
# NEXDEAL - CONTRACT ENGINE
# ==========================================

DEFAULT_RATES = {
    "INR": Decimal("1"),
    "USD": Decimal("84.5"),
    "EUR": Decimal("91"),
    "GBP": Decimal("106"),
}

CATEGORY_ALIASES = {
    "courier services": "courier",
    "cleaning services": "cleaning",
    "training workshops": "training",
    "led lighting": "led-lighting",
    "office chairs": "office-chairs",
}


def normalize_category(category):
    name = str(category).strip().lower()
    name = re.sub(r"[\s_-]+", " ", name)

    if name in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[name]

    return name.replace(" ", "-")


def get_contract_rules(supplier_name, category):
    """
    Load supplier contract overrides.

    Returns:
        status
        price_cap
        exchange_rates
        contract
    """

    suppliers = load_suppliers()

    supplier_key = str(supplier_name).strip().casefold()

    supplier = suppliers.get(supplier_key)

    if supplier is None:
        raise ValueError(
            f"Unknown supplier: {supplier_name}"
        )

    contract = supplier.get("contract") or ""
    status = supplier.get("status", "UNKNOWN")

    price_cap = None
    custom_rates = {}

    # --------------------------------------
    # 1. Supplier-specific price cap
    # --------------------------------------

    cap_match = re.search(
        r"price cap for\s+(.+?)\s+of\s+"
        r"\u20b9\s*([\d,]+(?:\.\d+)?)",
        contract,
        re.IGNORECASE
    )

    if cap_match:
        contract_category = normalize_category(
            cap_match.group(1)
        )

        requested_category = normalize_category(
            category
        )

        if contract_category == requested_category:
            price_cap = Decimal(
                cap_match.group(2).replace(",", "")
            )

    # --------------------------------------
    # 2. Supplier-specific exchange rates
    # --------------------------------------

    rate_matches = re.finditer(
        r"invoices in\s+(USD|EUR|GBP)\s+"
        r"are converted at\s+\u20b9\s*"
        r"([\d,]+(?:\.\d+)?)\s+per\s+"
        r"(USD|EUR|GBP)",
        contract,
        re.IGNORECASE
    )

    for match in rate_matches:
        currency = match.group(1).upper()
        denominator = match.group(3).upper()

        if currency != denominator:
            raise ValueError(
                "Contract currency mismatch"
            )

        custom_rates[currency] = Decimal(
            match.group(2).replace(",", "")
        )

    # --------------------------------------
    # 3. Combine default and custom rates
    # --------------------------------------

    rates = DEFAULT_RATES.copy()
    rates.update(custom_rates)

    return {
        "supplier": supplier["name"],
        "status": status,
        "price_cap": price_cap,
        "exchange_rates": rates,
        "contract": contract,
    }


# ==========================================
# TEST CONTRACT ENGINE
# ==========================================

if __name__ == "__main__":

    tests = [
        ("Indus Paper Mills", "courier"),
        ("Jupiter Devices", "monitors"),
        ("Arvind Office Supplies", "office-chairs"),
        ("Banyan Guarding", "laptops"),
    ]

    for supplier, category in tests:
        print("\nSupplier:", supplier)

        try:
            result = get_contract_rules(
                supplier,
                category
            )

            print("Status:", result["status"])
            print("Price cap:", result["price_cap"])
            print("Exchange rates:",
                  result["exchange_rates"])
            print("Contract:", result["contract"])

        except Exception as error:
            print("Error:", error)

