from __future__ import annotations
from django.db import models

# Create your models here.

from datetime import date
from django.db import models


class Member(models.Model):
    member_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20)
    monthly_amount = models.PositiveIntegerField(default=200)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.member_id} - {self.name}"


class Transaction(models.Model):
    """
    Transactions imported from bank/UPI statement.
    txn_uid is a hash-based unique key to avoid duplicate imports.
    """
    txn_uid = models.CharField(max_length=40, unique=True)
    original_txn_id = models.CharField(max_length=100, blank=True)
    txn_date = models.DateField()
    amount = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    source = models.CharField(max_length=200, blank=True)
    imported_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.txn_date} ₹{self.amount} ({self.txn_uid})"


class Due(models.Model):
    class Status(models.TextChoices):
        DUE = "DUE", "Due"
        PAID = "PAID", "Paid"
        REVIEW = "REVIEW", "Needs Review"

    # Store the first day of the month, e.g. 2026-01-01
    month = models.DateField()
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="dues")
    amount_due = models.PositiveIntegerField()
    reference_code = models.CharField(max_length=40)  # e.g. M001-202601
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DUE)

    matched_transaction = models.ForeignKey(
        Transaction, null=True, blank=True, on_delete=models.SET_NULL, related_name="matched_dues"
    )
    paid_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["month", "member"], name="uniq_due_month_member")
        ]
        indexes = [
            models.Index(fields=["month", "status"]),
            models.Index(fields=["reference_code"]),
        ]

    def __str__(self) -> str:
        return f"{self.month} {self.member.member_id} {self.status}"


class ExceptionItem(models.Model):
    """
    Keeped it simple for hackathon, stores candidate_member_ids as comma-separated text.
    future update needed
    """
    class Kind(models.TextChoices):
        REVIEW = "REVIEW", "Review"
        UNMAPPED = "UNMAPPED", "Unmapped"
        DUPLICATE = "DUPLICATE", "Duplicate"

    month = models.DateField()
    kind = models.CharField(max_length=10, choices=Kind.choices)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="exceptions")

    #  future replacement needed
    suggested_member = models.ForeignKey(Member, null=True, blank=True, on_delete=models.SET_NULL)
    candidate_member_ids = models.TextField(blank=True)  # e.g. "M001,M002,M005"
    reason = models.CharField(max_length=250, blank=True)

    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["month", "kind", "is_resolved"]),
        ]

    def __str__(self) -> str:
        return f"{self.month} {self.kind} {self.transaction.txn_uid}"
