from functools import lru_cache
from copy import deepcopy


from pathlib import Path
import re

BASE_DIR = Path(__file__).resolve().parent.parent
CATEGORY_DIR = BASE_DIR / "data" / "playbook" / "categories"


def read_number(text):
    text = text.replace(",", "")
    match = re.search(r"\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


@lru_cache(maxsize=1)
def _cached_load_categories():
    categories = {}

    for file in CATEGORY_DIR.glob("*.md"):
        content = file.read_text(encoding="utf-8-sig")

        def get_value(field):
            pattern = rf"\*\*{re.escape(field)}:\*\*\s*(.+)"
            match = re.search(pattern, content)
            return match.group(1).strip() if match else None

        categories[file.stem] = {
            "target": read_number(get_value("Target price") or ""),
            "walkaway": read_number(get_value("Walk-away price") or ""),
            "rounds": read_number(get_value("Negotiation rounds (R)") or ""),
            "beta": read_number(get_value("Concession exponent (β)") or ""),
            "approval_limit": read_number(get_value("Approval limit") or ""),
            "gst": read_number(get_value("GST rate") or ""),
            "unit": get_value("Normalized unit"),
        }

    return categories




def load_categories():
    return deepcopy(_cached_load_categories())


if __name__ == "__main__":
    categories = load_categories()

    print("Categories loaded:", len(categories))
    print("Laptops:", categories.get("laptops"))
