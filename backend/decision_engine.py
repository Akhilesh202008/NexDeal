import re
from decimal import Decimal, InvalidOperation

from negotiation_engine import calculate_negotiation_limit
from supplier_loader import load_suppliers


# ==========================================
# NEXDEAL - DECISION ENGINE
# ==========================================

def to_decimal(value):
    try:
        result = Decimal(str(value))

        if not result.is_finite():
            raise ValueError("Invalid numeric value")

        return result

    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Invalid numeric value")


def make_result(action, reason, counter_price=None):
    return {
        "action": action,
        "reason": reason,
        "counter_price": (
            int(counter_price)
            if counter_price is not None
            else None
        )
    }


def make_label(result):
    counter = result.get("counter_price")

    if counter is None:
        counter = ""

    return f"{result['action']}:{result['reason']}:{counter}"


# ==========================================
# PROMPT INJECTION DETECTION
# ==========================================

def detect_prompt_injection(text):
    text = text or ""

    patterns = [
        r"\[\s*(?:system|developer|assistant)\s*\]\s*(?:new\s+priority|instruction|override|approve|accept)",
        r"ignore\s+(all\s+)?previous\s+instructions",
        r"disregard\s+(the\s+)?(rules|instructions)",
        r"override\s+(the\s+)?(system|policy|rules)",
        r"bypass\s+(the\s+)?(security|policy|rules)",
        r"reveal\s+(the\s+)?system\s+prompt",
        r"you\s+are\s+now\s+(a|an)\b",
        r"system\s+note\s+to\s+(?:ai|assistant|agent)",
        r"language\s+model\s+processing\s+this\s+thread",
        r"(?:ai|bot|assistant|reviewer)\s*[:,]\s*(?:ignore|approve|override|disregard|mark)",
        r"approval\s+(?:has\s+)?already\s+been\s+granted",
        r"approval\s+already\s+granted",
        r"pre[\s-]?approved\s+by\s+.{0,50}cfo",
        r"\boutput\s+accept\b",
        r"\bmark\s+this\s+thread\s+as\s+accept\b",
        r"\bapprove\s+this\s+vendor\s+without\s+escalation\b",
        r"tell\s+(?:the\s+)?(?:ai|bot|model|reviewer)\s+to",

        # Extended security detection
        r"\b(?:cfo|ceo|management)\s+has\s+already\s+approved\b",
        r"\bai\s+(?:agent|assistant|bot)\s*[:,]\s*(?:please\s+)?(?:accept|approve|ignore|override)\b",
        r"\bautomated\s+approval\s+override\b",
        r"\bsystem\s+override\s*:\s*(?:approve|accept)\b",


        # Indirect automated approval manipulation
        r"\b(?:cfo|ceo|management)\s+(?:has\s+)?already\s+(?:signed\s+off|approved)\b",
        r"\b(?:bot|model|automated\s+reviewer)\b[\s\S]{0,150}\bmark\s+(?:it|this|the\s+deal)\s+(?:as\s+)?accepted\b",
        r"\b(?:bot|model|automated\s+reviewer)\b[\s\S]{0,150}\b(?:approve|accept)\b[\s\S]{0,40}\bwithout\s+(?:review|escalation)\b",



        r"\[\s*admin\s+override\s*\]",
        r"\bset\s+action\s*=\s*accept\b",
        r"\bskip\s+(?:the\s+)?playbook\s+checks\b",


        # Additional instruction manipulation
        r"\bignore\s+(?:(?:all|your|the)\s+)*previous\s+instructions\b",
        r"\b(?:reviewing|automated)\s+(?:assistant|agent|reviewer)\s+should\s+(?:accept|approve)\b",
        r"\bpre[\s-]?approved\b[\s\S]{0,100}\b(?:assistant|bot|reviewer)\b[\s\S]{0,40}\b(?:accept|approve)\b",

        # Hindi-language prompt injection
        r"\bAI\s+\u0938\u0939\u093e\u092f\u0915[\s\S]{0,100}\b(?:ACCEPT|APPROVE)\b",

        # Romanized Hindi / Hinglish
        r"\b(?:instructions|rules)\s+ignore\s+karo\b",
        r"\bignore\s+karo\s+(?:previous|all)\s+instructions\b",
        r"\bai\s+(?:bot|agent|assistant)\b.{0,60}\b(?:approve|accept)\s+karo\b",
    ]

    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in patterns
    )


# ==========================================
# BANNED CONTRACT TERMS
# ==========================================

def detect_banned_terms(text):
    text = (text or "").lower()

    # Convert written percentages to numbers.
    number_words = {
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
        "eighty": 80, "ninety": 90,
        "hundred": 100
    }

    def convert_percentage(match):
        words = match.group(1).replace("-", " ").split()

        value = sum(number_words[w] for w in words)

        if words == ["one", "hundred"]:
            value = 100

        return str(value) + "%"

    word_pattern = "|".join(number_words)

    text = re.sub(
        rf"\b((?:{word_pattern})(?:[- ](?:{word_pattern}))?)\s+percent\b",
        convert_percentage,
        text
    )

    # Explicitly excluded clauses are allowed.
    negated_patterns = [
        r"\bwe\s+are\s+not\s+asking\s+for\s+exclusivity\b",
        r"\bnot\s+asking\s+for\s+exclusivity\b",
        r"\bno\s+exclusivity\b",
        r"\bwithout\s+exclusivity\b",
        r"\bnot\s+requiring\s+exclusivity\b",

        r"\bthere\s+is\s+no\s+automatic\s+renewal\b",
        r"\bno\s+automatic\s+renewal\b",
        r"\bno\s+auto[\s-]?renewal\b",
        r"\bwithout\s+automatic\s+renewal\b",
        r"\brenewal\s+only\s+if\s+both\s+parties\s+sign\s+again\b",

        r"\bno\s+unlimited\s+liability\b",
        r"\bwithout\s+unlimited\s+liability\b",
    ]

    for pattern in negated_patterns:
        text = re.sub(
            pattern,
            "clause expressly excluded",
            text
        )

    banned_patterns = [
        r"\bauto[\s-]?renew(?:s|al|ed|ing)?\b",
        r"\bautomatic(?:ally)?\s+renew",
        r"\brenews?\s+on\s+its\s+own\b",
        r"\bcontinues?\s+(?:from\s+)?year\s+to\s+year\s+unless\b",

        r"\bunlimited\s+liability\b",

        r"\bexclusive\s+(?:supplier|provider|agreement)\b",
        r"\bexclusivity\b",
        r"\bmust\s+(?:buy|purchase)\s+only\s+from\b",
    ]

    for pattern in banned_patterns:
        if re.search(pattern, text):
            return True

    # Advance payments above 30% are prohibited.
    advance_patterns = [
        r"(advance|upfront|prepayment|deposit)(?:\s+\w+){0,5}?\s+(\d+(?:\.\d+)?)\s*%",
        r"(\d+(?:\.\d+)?)\s*%(?:\s+\w+){0,4}?\s+(?:advance|upfront|prepayment|deposit)",
    ]

    for index, pattern in enumerate(advance_patterns):
        for match in re.finditer(pattern, text):

            if index == 0:
                percentage = Decimal(match.group(2))
            else:
                percentage = Decimal(match.group(1))

            if percentage > Decimal("30"):
                return True

    return False


# ==========================================
# MAIN DECISION ENGINE
# ==========================================

def make_decision(
    supplier,
    category,
    price=None,
    currency="INR",
    quantity=1,
    email_text="",
    date=None,
    round_number=1,
    latest_message=None,
    gst_inclusive=False,
    is_total_price=False,
    discount_percent=None,
    **kwargs
):

    # --------------------------------------
    # 1. MISSING INFORMATION
    # --------------------------------------

    if price is None or str(price).strip() == "":
        return make_result(
            "ESCALATE",
            "MISSING_INFO"
        )

    currency = str(currency).upper().strip()

    if currency not in ("INR", "USD", "EUR", "GBP"):
        return make_result(
            "ESCALATE",
            "MISSING_INFO"
        )

    try:
        amount = to_decimal(price)
        qty = int(quantity)
        current_round = int(round_number)

        if amount < 0 or qty < 1 or current_round < 1:
            raise ValueError("Invalid offer")

        if to_decimal(quantity) != qty:
            raise ValueError("Invalid quantity")

        if to_decimal(round_number) != current_round:
            raise ValueError("Invalid round")

    except (ValueError, TypeError, InvalidOperation, OverflowError):
        return make_result(
            "ESCALATE",
            "MISSING_INFO"
        )

    if not date:
        return make_result(
            "ESCALATE",
            "MISSING_INFO"
        )

    suppliers = load_suppliers()

    supplier_data = suppliers.get(
        str(supplier).strip().casefold()
    )

    if supplier_data is None:
        return make_result(
            "ESCALATE",
            "MISSING_INFO"
        )

    # --------------------------------------
    # 2. BLACKLISTED SUPPLIER
    # --------------------------------------

    if supplier_data["status"] == "BLACKLISTED":
        return make_result(
            "REJECT",
            "BLACKLISTED_SUPPLIER"
        )

    # --------------------------------------
    # 3. PROMPT INJECTION
    # --------------------------------------

    current_message = (
        latest_message
        if latest_message is not None
        else email_text
    )

    if (
        detect_prompt_injection(email_text)
        or detect_prompt_injection(current_message)
    ):
        return make_result(
            "ESCALATE",
            "PROMPT_INJECTION"
        )

    # --------------------------------------
    # 4. BANNED CONTRACT TERMS
    # --------------------------------------

    if detect_banned_terms(current_message):
        return make_result(
            "ESCALATE",
            "BANNED_TERM"
        )

    # --------------------------------------
    # 5. LOAD NEGOTIATION RULES
    # --------------------------------------

    try:
        negotiation = calculate_negotiation_limit(
            category=category,
            supplier=supplier,
            thread_date=date,
            round_number=current_round
        )

    except (ValueError, KeyError, TypeError):
        return make_result(
            "ESCALATE",
            "MISSING_INFO"
        )

    limit = to_decimal(negotiation["limit"])
    rounds = int(negotiation["rounds"])

    rates = negotiation["exchange_rates"]

    if currency not in rates:
        return make_result(
            "ESCALATE",
            "MISSING_INFO"
        )

    # --------------------------------------
    # 6. NORMALIZE SUPPLIER PRICE
    # --------------------------------------

    offered_inr = amount * to_decimal(
        rates[currency]
    )

    # Apply eligible discounts.
    if discount_percent is not None:

        try:
            discount = to_decimal(discount_percent)

        except ValueError:
            return make_result(
                "ESCALATE",
                "MISSING_INFO"
            )

        if discount < 0 or discount > 100:
            return make_result(
                "ESCALATE",
                "MISSING_INFO"
            )

        offered_inr *= (
            Decimal("1")
            - discount / Decimal("100")
        )

    # Convert total prices to unit prices.
    if is_total_price:
        offered_inr /= Decimal(qty)

    # Remove included GST.
    if gst_inclusive:

        gst = to_decimal(negotiation["gst"])

        offered_inr /= (
            Decimal("1")
            + gst / Decimal("100")
        )

    # --------------------------------------
    # 7. NEGOTIATION PRICE DECISION
    # --------------------------------------

    if offered_inr > limit:

        if current_round >= rounds:
            return make_result(
                "REJECT",
                "ABOVE_WALKAWAY"
            )

        return make_result(
            "COUNTER",
            "COUNTER_OFFER",
            negotiation["counter_price"]
        )

    # --------------------------------------
    # 8. APPROVAL LIMIT
    # --------------------------------------

    total_value = offered_inr * Decimal(qty)

    approval_limit = to_decimal(
        negotiation["approval_limit"]
    )

    if total_value > approval_limit:
        return make_result(
            "ESCALATE",
            "OVER_APPROVAL_LIMIT"
        )

    # --------------------------------------
    # 9. ACCEPTABLE OFFER
    # --------------------------------------

    return make_result(
        "ACCEPT",
        "ACCEPTABLE_PRICE"
    )