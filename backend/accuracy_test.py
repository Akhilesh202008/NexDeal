
import csv
from pathlib import Path

from email_parser import extract_email_data
from decision_engine import make_decision, make_label


# ==========================================
# NEXDEAL - OFFICIAL ACCURACY TEST
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

THREADS_PATH = DATA_DIR / "sample_threads.csv"
ANSWERS_PATH = DATA_DIR / "sample_answers.csv"
RESULTS_PATH = DATA_DIR / "accuracy_results.csv"


def load_csv(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required CSV file not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        return list(csv.DictReader(file))


def get_expected_answers(rows):
    answers = {}

    for row in rows:
        thread_id = row["thread_id"].strip()

        # Supports either 'label' or
        # 'expected_label' column names.
        label = (
            row.get("label")
            or row.get("expected_label")
            or row.get("decision")
            or ""
        ).strip()

        answers[thread_id] = label

    return answers


def evaluate_thread(row):
    # --------------------------------------
    # 1. Extract supplier email information
    # --------------------------------------

    parsed = extract_email_data(
        row["supplier_message"],
        category=row["category"],
        quantity=int(row["quantity"])
    )

    # --------------------------------------
    # 2. Determine applicable discount
    # --------------------------------------

    discount = parsed.get("discount_percent")
    threshold = parsed.get("discount_threshold")

    quantity = int(row["quantity"])

    if (
        discount is not None
        and threshold is not None
        and quantity < threshold
    ):
        discount = None

    # --------------------------------------
    # 3. Generate decision
    # --------------------------------------

    result = make_decision(
        supplier=row["supplier"],
        category=row["category"],
        price=parsed["price"],
        currency=parsed["currency"],
        quantity=quantity,
        email_text=parsed["email_text"],
        latest_message=parsed["latest_message"],
        date=row["date"],
        round_number=int(
    row.get("round_number") or row.get("round") or 1
),
        gst_inclusive=parsed.get(
            "gst_inclusive", False
        ),
        is_total_price=parsed.get(
            "is_total_price", False
        ),
        discount_percent=discount
    )

    return result, parsed


def main():
    print("=" * 60)
    print("NEXDEAL - OFFICIAL SAMPLE ACCURACY TEST")
    print("=" * 60)

    threads = load_csv(THREADS_PATH)
    answer_rows = load_csv(ANSWERS_PATH)

    expected_answers = get_expected_answers(
        answer_rows
    )

    total = 0
    correct = 0
    incorrect = 0
    errors = 0

    results = []

    for row in threads:
        thread_id = row["thread_id"].strip()

        if thread_id not in expected_answers:
            continue

        total += 1

        expected = expected_answers[thread_id]

        try:
            decision, parsed = evaluate_thread(row)

            predicted = make_label(decision)

            # A review flag means the parser
            # could not confidently resolve
            # the supplier's commercial offer.
            # Security and missing-info decisions
            # can still be evaluated.
            if parsed.get("needs_review", False):
                allowed_reasons = {
                    "PROMPT_INJECTION",
                    "BANNED_TERM",
                    "BLACKLISTED_SUPPLIER",
                    "MISSING_INFO",
                }

                if decision["reason"] not in allowed_reasons:
                    raise ValueError(
                        parsed.get("review_reason")
                        or "Manual review required"
                    )

            matched = predicted == expected

            if matched:
                correct += 1
                status = "PASS"
            else:
                incorrect += 1
                status = "FAIL"

            error_message = ""

        except Exception as exc:
            predicted = "NO DECISION"
            status = "ERROR"
            error_message = str(exc)
            errors += 1

        print(f"\n{thread_id} | {status}")
        print(f"  Expected : {expected}")
        print(f"  Predicted: {predicted}")

        if error_message:
            print(f"  Error    : {error_message}")

        results.append({
            "thread_id": thread_id,
            "expected": expected,
            "predicted": predicted,
            "status": status,
            "error": error_message,
        })

    # --------------------------------------
    # 4. Save detailed results
    # --------------------------------------

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with RESULTS_PATH.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "thread_id",
                "expected",
                "predicted",
                "status",
                "error",
            ]
        )

        writer.writeheader()
        writer.writerows(results)

    # --------------------------------------
    # 5. Final accuracy report
    # --------------------------------------

    accuracy = (
        correct / total * 100
        if total > 0
        else 0
    )

    print("\n" + "=" * 60)
    print("FINAL ACCURACY REPORT")
    print("=" * 60)

    print(
        "Official answers       :",
        len(expected_answers)
    )
    print(
        "Matched sample threads :",
        total
    )
    print(
        "Correct predictions    :",
        correct
    )
    print(
        "Incorrect predictions  :",
        incorrect + errors
    )
    print(
        "Processing errors      :",
        errors
    )
    print(
        "Exact-match accuracy   :",
        f"{accuracy:.2f}%"
    )
    print(
        "Results saved to       :",
        RESULTS_PATH
    )

    print("=" * 60)


if __name__ == "__main__":
    main()
