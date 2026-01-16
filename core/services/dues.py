from __future__ import annotations

from datetime import date
from django.db import transaction

from core.models import Member, Due


def month_to_yyyymm(month: date) -> str:
    return f"{month.year:04d}{month.month:02d}"


def reference_code(member_id: str, month: date) -> str:
    return f"{member_id.upper()}-{month_to_yyyymm(month)}"


@transaction.atomic
def generate_dues_for_month(month: date) -> int:

    members = Member.objects.filter(is_active=True).order_by("member_id")
    touched = 0

    for m in members:
        ref = reference_code(m.member_id, month)
        due, created = Due.objects.get_or_create(
            month=month,
            member=m,
            defaults={
                "amount_due": m.monthly_amount,
                "reference_code": ref,
                "status": Due.Status.DUE,
            },
        )
        if created:
            touched += 1
            continue

        # Update only if not PAID
        if due.status != Due.Status.PAID:
            changed = False
            if due.amount_due != m.monthly_amount:
                due.amount_due = m.monthly_amount
                changed = True
            if due.reference_code != ref:
                due.reference_code = ref
                changed = True
            if changed:
                due.save(update_fields=["amount_due", "reference_code"])
                touched += 1

    return touched
