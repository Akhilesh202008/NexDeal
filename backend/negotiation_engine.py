
from decimal import Decimal

from amendment_engine import get_category_rules
from contract_engine import get_contract_rules
from pricing_engine import calculate_limit, round_rupee


# ==========================================
# NEXDEAL - NEGOTIATION ENGINE
# ==========================================

def calculate_negotiation_limit(
    category,
    supplier,
    thread_date,
    round_number
):
    """
    Calculate negotiation limits using:

    1. Category rules
    2. Dated amendments
    3. Supplier contract overrides
    4. Probation restrictions
    5. Negotiation round limits
    """

    # --------------------------------------
    # 1. Load category rules
    # --------------------------------------

    rules = get_category_rules(
        category,
        thread_date
    )

    # --------------------------------------
    # 2. Load supplier contract rules
    # --------------------------------------

    contract = get_contract_rules(
        supplier,
        category
    )

    target = Decimal(str(rules["target"]))
    walkaway = Decimal(str(rules["walkaway"]))
    rounds = int(rules["rounds"])
    approval_limit = Decimal(
        str(rules["approval_limit"])
    )
    gst = Decimal(str(rules["gst"]))

    status = contract["status"]

    # --------------------------------------
    # 3. Apply supplier contract price cap
    # --------------------------------------

    price_cap = contract.get("price_cap")

    if price_cap is not None:
        cap = Decimal(str(price_cap))
        walkaway = cap

    # --------------------------------------
    # 4. Calculate round-specific limit
    # --------------------------------------

    calculated_limit = Decimal(
        str(
            calculate_limit(
                category=category,
                round_number=round_number,
                probation=(status == "PROBATION"),
                thread_date=thread_date,
                supplier_name=supplier
            )
        )
    )

    # --------------------------------------
    # 5. Enforce contract price cap
    # --------------------------------------

    if price_cap is not None and round_number >= rounds:
        final_limit = walkaway
    else:
        final_limit = min(calculated_limit, walkaway)

    # --------------------------------------
    # 6. Apply probation restriction
    # --------------------------------------

    if status == "PROBATION":
        final_limit = min(
            final_limit,
            target
        )

    # --------------------------------------
    # 7. Validate values
    # --------------------------------------

    if final_limit < 0:
        raise ValueError(
            "Negotiation limit cannot be negative"
        )

    if rounds < 1:
        raise ValueError(
            "Negotiation rounds must be positive"
        )

    if approval_limit < 0:
        raise ValueError(
            "Approval limit cannot be negative"
        )

    # --------------------------------------
    # 8. Return negotiation details
    # --------------------------------------

    return {
        "limit": final_limit,
        "counter_price": round_rupee(final_limit),
        "target": target,
        "walkaway": walkaway,
        "approval_limit": approval_limit,
        "gst": gst,
        "rounds": rounds,
        "supplier_status": status,
        "exchange_rates": contract["exchange_rates"],
    }


# ==========================================
# TEST NEGOTIATION ENGINE
# ==========================================

if __name__ == "__main__":

    result = calculate_negotiation_limit(
        category="laptops",
        supplier="Banyan Guarding",
        thread_date="2026-11-23",
        round_number=4
    )

    print("=" * 45)
    print("NEXDEAL NEGOTIATION ENGINE")
    print("=" * 45)

    print("Negotiation limit:", result["limit"])
    print("Counter price:", result["counter_price"])
    print("Supplier status:", result["supplier_status"])
    print("Target:", result["target"])
    print("Walkaway:", result["walkaway"])
    print("Approval limit:", result["approval_limit"])
    print("GST:", result["gst"])
    print("Rounds:", result["rounds"])


