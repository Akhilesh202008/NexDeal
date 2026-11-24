
import csv
import re

from io import StringIO
from pathlib import Path
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from decision_engine import make_decision, make_label
from accuracy_test import evaluate_thread


# ==========================================
# NEXDEAL - FASTAPI BACKEND
# ==========================================

app = FastAPI(
    title="NexDeal AI",
    description="AI-powered procurement negotiation engine",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "data" / "threads.csv"


# ==========================================
# REQUEST MODELS
# ==========================================

class NegotiationRequest(BaseModel):

    thread_id: str
    supplier: str
    category: str

    price: Optional[Decimal] = Field(
        default=None,
        ge=0
    )

    currency: str = "INR"

    quantity: int = Field(
        default=1,
        ge=1
    )

    email_text: str = ""

    supplier_message: Optional[str] = None

    latest_message: Optional[str] = None

    date: Optional[str] = None

    round_number: int = Field(
        default=1,
        ge=1
    )

    gst_inclusive: bool = False
    is_total_price: bool = False

    discount_percent: Optional[Decimal] = None

    extra: Dict[str, Any] = Field(
        default_factory=dict
    )


class BatchRequest(BaseModel):

    threads: List[NegotiationRequest]


# ==========================================
# LABEL FORMATTING
# ==========================================

LABEL_PATTERN = re.compile(
    r"^(ACCEPT|COUNTER|REJECT|ESCALATE):"
    r"([A-Z][A-Z0-9_]*):([0-9]*)$"
)


def format_label(result):

    if isinstance(result, str):

        label = result.strip()

    elif isinstance(result, dict):

        if "label" in result:

            label = str(
                result["label"]
            ).strip()

        else:

            action = str(
                result.get("action", "")
            ).upper()

            reason = str(
                result.get("reason", "")
            ).upper()

            counter = result.get(
                "counter_price"
            )

            if counter is None:
                counter = ""

            label = f"{action}:{reason}:{counter}"

    else:

        raise ValueError(
            "Unsupported decision result"
        )

    match = LABEL_PATTERN.fullmatch(label)

    if not match:

        raise ValueError(
            f"Invalid decision label: {label}"
        )

    action, reason, counter = match.groups()

    if action == "COUNTER" and not counter:

        raise ValueError(
            "COUNTER requires a price"
        )

    if action != "COUNTER" and counter:

        raise ValueError(
            "Only COUNTER can have a counter price"
        )

    return label


# ==========================================
# SHARED ANALYSIS PIPELINE
# ==========================================

def analyze_thread(thread: NegotiationRequest):

    payload = thread.model_dump(
        exclude={
            "thread_id",
            "extra",
            "supplier_message"
        }
    )

    allowed_extra = {
        "gst_inclusive",
        "is_total_price",
        "discount_percent",
        "latest_message",
        "round_number",
        "date",
    }

    for key, value in thread.extra.items():

        if key in allowed_extra:
            payload[key] = value

    raw_message = (
        thread.supplier_message
        or payload.get("email_text")
        or payload.get("latest_message")
        or ""
    )

    # Raw supplier email analysis.
    # Use the same pipeline as CSV predictions.
    if payload.get("price") is None and raw_message:

        row = {
            "thread_id": thread.thread_id,
            "supplier": thread.supplier,
            "category": thread.category,
            "quantity": thread.quantity,
            "supplier_message": raw_message,
            "date": payload.get("date"),
            "round_number": payload.get(
                "round_number", 1
            ),
        }

        result, parsed = evaluate_thread(row)

        if parsed.get("needs_review"):

            allowed_reasons = {
                "PROMPT_INJECTION",
                "BANNED_TERM",
                "BLACKLISTED_SUPPLIER",
                "MISSING_INFO",
            }

            if result["reason"] not in allowed_reasons:

                raise ValueError(
                    parsed.get("review_reason")
                    or "Manual review required"
                )

    # Structured price analysis.
    # Preserves compatibility with existing frontend.
    else:

        if raw_message:
            payload["email_text"] = raw_message

        result = make_decision(**payload)

    return {
        "thread_id": thread.thread_id,
        "label": format_label(result)
    }


# ==========================================
# BASIC ENDPOINTS
# ==========================================

@app.get("/")
def home():

    return {
        "project": "NexDeal AI",
        "status": "running",
        "version": "2.1.0"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "NexDeal Backend"
    }


# ==========================================
# SINGLE THREAD ANALYSIS
# ==========================================

@app.post("/analyze")
def analyze(request: NegotiationRequest):

    try:

        return analyze_thread(request)

    except Exception as error:

        raise HTTPException(
            status_code=422,
            detail=str(error)
        )


# ==========================================
# BATCH ANALYSIS
# ==========================================

@app.post("/batch")
def batch_analyze(request: BatchRequest):

    results = []

    for thread in request.threads:

        try:

            results.append(
                analyze_thread(thread)
            )

        except Exception as error:

            raise HTTPException(
                status_code=422,
                detail={
                    "thread_id": thread.thread_id,
                    "error": str(error)
                }
            )

    return {
        "total": len(results),
        "results": results
    }


# ==========================================
# CSV EXPORT
# ==========================================

@app.post("/export")
def export_csv(request: BatchRequest):

    results = []

    for thread in request.threads:

        try:

            results.append(
                analyze_thread(thread)
            )

        except Exception as error:

            raise HTTPException(
                status_code=422,
                detail={
                    "thread_id": thread.thread_id,
                    "error": str(error)
                }
            )

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "thread_id",
        "label"
    ])

    for result in results:

        writer.writerow([
            result["thread_id"],
            result["label"]
        ])

    csv_content = output.getvalue()
    output.close()

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
            'attachment; filename="nexdeal_submission.csv"'
        }
    )


# ==========================================
# REAL DATASET PROCESSING
# ==========================================

@app.post("/process-csv")
def process_csv(
    limit: int = 10,
    offset: int = 0
):

    if limit < 1 or limit > 100 or offset < 0:

        raise HTTPException(
            status_code=422,
            detail="Limit must be 1-100 and offset >= 0"
        )

    if not DATASET_PATH.is_file():

        raise HTTPException(
            status_code=404,
            detail="Dataset not found"
        )

    results = []
    review_queue = []
    processed = 0

    with DATASET_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        columns = set(
            reader.fieldnames or []
        )

        required = {
            "thread_id",
            "date",
            "supplier",
            "category",
            "quantity",
            "supplier_message"
        }

        if not required.issubset(columns) or not (
            {"round", "round_number"} & columns
        ):

            raise HTTPException(
                status_code=422,
                detail="Dataset is missing required columns"
            )

        for index, row in enumerate(reader):

            if index < offset:
                continue

            if index >= offset + limit:
                break

            processed += 1

            thread_id = row["thread_id"].strip()

            try:

                decision, parsed = evaluate_thread(row)

                label = format_label(decision)

                if parsed.get("needs_review"):

                    review_queue.append({
                        "thread_id": thread_id,
                        "reason": (
                            parsed.get("review_reason")
                            or "Parser review required"
                        )
                    })

                    allowed_reasons = {
                        "PROMPT_INJECTION",
                        "BANNED_TERM",
                        "BLACKLISTED_SUPPLIER",
                        "MISSING_INFO",
                    }

                    if decision["reason"] not in allowed_reasons:
                        continue

                results.append({
                    "thread_id": thread_id,
                    "label": label,
                    "extracted_price": (
                        str(parsed["price"])
                        if parsed.get("price") is not None
                        else None
                    ),
                    "currency": parsed.get("currency")
                })

            except Exception as error:

                review_queue.append({
                    "thread_id": thread_id,
                    "reason": str(error)
                })

    return {
        "processed": processed,
        "decisions_generated": len(results),
        "needs_review": len(review_queue),
        "results": results,
        "review_queue": review_queue
    }
