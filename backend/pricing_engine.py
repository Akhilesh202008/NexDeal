
from decimal import Decimal, ROUND_HALF_UP

from amendment_engine import get_category_rules
from contract_engine import get_contract_rules


# ==========================================
# NEXDEAL - PRICING ENGINE
# ==========================================

def to_decimal(value):
    """Convert numeric values safely to Decimal."""
    result = Decimal(str(value))

    if not result.is_finite():
        raise ValueError("Price must be finite")

    return result


def round_rupee(price):
    """Round to nearest rupee, with .5 rounded up."""
    return int(
        to_decimal(price).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP
        )
    )


def calculate_limit(
    category,
    round_number,
    probation=False,
    thread_date=None,
    supplier_name=None
):
    """
    Calculate maximum acceptable unit price using:

    1. Category pricing rules
    2. Effective dated amendments
    3. Supplier contract price caps
    4. Probation restrictions
    5. Round-based concession formula
    """

    if thread_date is None:
        raise ValueError(
            "Thread date is required for amendment rules"
        )

    # --------------------------------------
    # 1. Load effective category rules
    # --------------------------------------

    rules = get_category_rules(
        category,
        thread_date
    )

    target = to_decimal(rules["target"])
    walkaway = to_decimal(rules["walkaway"])
    rounds = int(rules["rounds"])
    beta = to_decimal(rules["beta"])

    # --------------------------------------
    # 2. Load supplier contract rules
    # --------------------------------------

    price_cap = None

    if supplier_name:
        contract = get_contract_rules(
            supplier_name,
            category
        )

        if contract["price_cap"] is not None:
            price_cap = to_decimal(
                contract["price_cap"]
            )
            walkaway = price_cap

        if contract["status"] == "PROBATION":
            probation = True

    # --------------------------------------
    # 3. Validate parameters
    # --------------------------------------

    if target < 0 or walkaway < 0:
        raise ValueError(
            "Prices cannot be negative"
        )

    if rounds < 1:
        raise ValueError(
            "Negotiation rounds must be positive"
        )

    if beta <= 0:
        raise ValueError(
            "Concession exponent must be positive"
        )

    if price_cap is not None and price_cap < 0:
        raise ValueError(
            "Supplier price cap cannot be negative"
        )

    r = int(round_number)

    if r < 1 or r > rounds:
        raise ValueError(
            f"Round must be between 1 and {rounds}"
        )

    # --------------------------------------
    # 4. Calculate concession limit
    # --------------------------------------

    if probation:
        limit = target

    elif rounds == 1:
        limit = walkaway

    else:
        fraction = (
            Decimal(r - 1) /
            Decimal(rounds - 1)
        )

        limit = target + (
            (walkaway - target) *
            (fraction ** beta)
        )

    # --------------------------------------
    # 5. Apply supplier price cap
    # --------------------------------------

    if price_cap is not None:
        limit = min(limit, price_cap)

    # --------------------------------------
    # 6. Return final limit
    # --------------------------------------

    return limit


# ==========================================
# TEST PRICING ENGINE
# ==========================================

if __name__ == "__main__":

    print("=" * 45)
    print("NEXDEAL PRICING ENGINE")
    print("=" * 45)

    for r in range(1, 5):

        price = calculate_limit(
            category="laptops",
            round_number=r,
            thread_date="2026-11-01"
        )

        print(
            f"Round {r}: "
            f"INR {price:.2f} | "
            f"Counter: INR {round_rupee(price)}"
        )

    probation_price = calculate_limit(
        category="laptops",
        round_number=4,
        probation=True,
        thread_date="2026-11-01"
    )

    print(
        "\nProbation round 4:",
        probation_price
    )

