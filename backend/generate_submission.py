import csv
from pathlib import Path
from accuracy_test import evaluate_thread
from decision_engine import make_label

data = Path(__file__).resolve().parent.parent / "data"
rows = list(csv.DictReader((data / "threads.csv").open(encoding="utf-8-sig", newline="")))
results = []
errors = []

for row in rows:
    try:
        decision, parsed = evaluate_thread(row)
        if parsed.get("needs_review") and decision.get("reason") not in {"PROMPT_INJECTION", "BANNED_TERM", "BLACKLISTED_SUPPLIER", "MISSING_INFO"}:
            raise ValueError(parsed.get("review_reason") or "Parser review required")
        label = make_label(decision)
        parts = label.split(":")
        if len(parts) != 3 or parts[0] not in {"ACCEPT", "COUNTER", "REJECT", "ESCALATE"} or (parts[0] == "COUNTER" and not parts[2].isdigit()) or (parts[0] != "COUNTER" and parts[2] != ""):
            raise ValueError("Invalid label: " + label)
        results.append({"thread_id": row["thread_id"].strip(), "label": label})
    except Exception as e:
        errors.append({"thread_id": row["thread_id"], "error": str(e)})

if errors:
    with (data / "submission_errors.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["thread_id", "error"])
        writer.writeheader()
        writer.writerows(errors)
    print(f"STOP: {len(errors)} errors. Check submission_errors.csv")
elif len(results) != 2000 or len({r["thread_id"] for r in results}) != 2000:
    print(f"STOP: Expected 2000 unique threads, got {len(results)} rows")
else:
    with (data / "submission.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["thread_id", "label"])
        writer.writeheader()
        writer.writerows(results)
    print(f"SUCCESS: {len(results)} predictions saved to {data / 'submission.csv'}")
