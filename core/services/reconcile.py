from __future__ import annotations

import re
from datetime import date
from typing import List, Optional

from django.db import transaction
from core.models import Due, Transaction, ExceptionItem, Member


REF_REGEX = re.compile(r"([A-Z0-9_]{1,20})-(\d{6})", re.IGNORECASE)


def extract_refs(desc: str) -> List[str]:
    desc = (desc or "").upper()
    return [f"{m.group(1).upper()}-{m.group(2)}" for m in REF_REGEX.finditer(desc)]


def month_to_yyyymm(month: date) -> str:
    return f"{month.year:04d}{month.month:02d}"


@transaction.atomic
def reconcile_month(month: date) -> dict:
    """
    Reconcile imported transactions against dues for the month.
    Creates ExceptionItem for REVIEW/UNMAPPED/DUPLICATE.
    Returns counts dict.
    """
    yyyymm = month_to_yyyymm(month)

    dues = Due.objects.select_related("member").filter(month=month)
    due_by_ref = {d.reference_code.upper(): d for d in dues}

    # Only consider transactions not already linked to a due for this month
    linked_txn_ids = set(
        Due.objects.filter(month=month, matched_transaction__isnull=False)
        .values_list("matched_transaction__txn_uid", flat=True)
    )

    auto_paid = 0
    review = 0
    unmapped = 0
    duplicate = 0

    for t in Transaction.objects.all().order_by("txn_date", "imported_at"):
        if t.txn_uid in linked_txn_ids:
            continue

        refs = extract_refs(t.description)

        matched = False

        # Reference-based
        for ref in refs:
            # If statement has month mismatch (ref ends with different yyyymm), ignore it for this month
            if not ref.endswith(yyyymm):
                continue

            if ref in due_by_ref:
                d = due_by_ref[ref]
                if d.status == Due.Status.PAID or d.matched_transaction_id is not None:
                    ExceptionItem.objects.get_or_create(
                        month=month,
                        kind=ExceptionItem.Kind.DUPLICATE,
                        transaction=t,
                        defaults={"reason": f"Duplicate payment for {ref}"},
                    )
                    duplicate += 1
                    matched = True
                    break

                d.status = Due.Status.PAID
                d.matched_transaction = t
                d.paid_date = t.txn_date
                d.save(update_fields=["status", "matched_transaction", "paid_date"])
                auto_paid += 1
                matched = True
                break

        if matched:
            continue

        # Amount-based candidates among unpaid dues
        candidates = Due.objects.filter(month=month, status__in=[Due.Status.DUE, Due.Status.REVIEW], amount_due=t.amount)

        if candidates.count() == 1:
            c = candidates.first()
            # mark due as REVIEW linked to this txn (admin can confirm)
            c.status = Due.Status.REVIEW
            c.matched_transaction = t
            c.save(update_fields=["status", "matched_transaction"])

            ExceptionItem.objects.get_or_create(
                month=month,
                kind=ExceptionItem.Kind.REVIEW,
                transaction=t,
                defaults={
                    "suggested_member": c.member,
                    "candidate_member_ids": c.member.member_id,
                    "reason": "No reference; unique amount match",
                },
            )
            review += 1
        elif candidates.count() > 1:
            cand_ids = ",".join(list(candidates.values_list("member__member_id", flat=True)))
            ExceptionItem.objects.get_or_create(
                month=month,
                kind=ExceptionItem.Kind.REVIEW,
                transaction=t,
                defaults={
                    "suggested_member": None,
                    "candidate_member_ids": cand_ids,
                    "reason": "No reference; multiple candidates with same amount",
                },
            )
            review += 1
        else:
            ExceptionItem.objects.get_or_create(
                month=month,
                kind=ExceptionItem.Kind.UNMAPPED,
                transaction=t,
                defaults={"reason": "No reference match and no amount match"},
            )
            unmapped += 1

    return {"auto_paid": auto_paid, "review": review, "unmapped": unmapped, "duplicate": duplicate}
