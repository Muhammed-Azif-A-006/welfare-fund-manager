from __future__ import annotations

import csv
import hashlib
from datetime import datetime, date
from typing import Optional

from core.models import Transaction


def _parse_date(value: str) -> date:
    """
    Accepts common formats; for hackathon keep it strict to YYYY-MM-DD.
    """
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def make_txn_uid(original_txn_id: str, txn_date: date, amount: int, description: str, source: str) -> str:
    base = f"{original_txn_id}|{txn_date.isoformat()}|{amount}|{description}|{source}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def import_statement_csv(
    filepath: str,
    source: str = "",
    col_txn_id: str = "txn_id",
    col_date: str = "txn_date",
    col_amount: str = "amount",
    col_desc: str = "description",
) -> int:
    """
    Imports CSV into Transaction table.
    Returns number of rows processed (not necessarily inserted).
    """
    count = 0
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            original_txn_id = (row.get(col_txn_id) or "").strip() or f"ROW{count+1}"
            txn_date = _parse_date(row[col_date])
            amount = int(float(row[col_amount]))
            description = (row.get(col_desc) or "").strip()

            txn_uid = make_txn_uid(original_txn_id, txn_date, amount, description, source)

            Transaction.objects.get_or_create(
                txn_uid=txn_uid,
                defaults={
                    "original_txn_id": original_txn_id,
                    "txn_date": txn_date,
                    "amount": amount,
                    "description": description,
                    "source": source,
                },
            )
            count += 1
    return count

