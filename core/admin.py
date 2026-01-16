
from __future__ import annotations
from datetime import date
from django.contrib import admin, messages
from django.utils import timezone

from core.models import Member, Due, Transaction, ExceptionItem
from core.services.dues import generate_dues_for_month
from core.services.reconcile import reconcile_month


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("member_id", "name", "phone", "monthly_amount", "is_active")
    list_filter = ("is_active",)
    search_fields = ("member_id", "name", "phone")
    ordering = ("member_id",)


@admin.register(Due)
class DueAdmin(admin.ModelAdmin):
    list_display = ("month", "member", "amount_due", "reference_code", "status", "paid_date")
    list_filter = ("month", "status")
    search_fields = ("member__member_id", "member__name", "reference_code")
    ordering = ("-month", "member__member_id")
    actions = ["action_generate_dues_for_selected_month"]

    @admin.action(description="Generate/Update dues for selected month (uses month of first selected row)")
    def action_generate_dues_for_selected_month(self, request, queryset):
        if not queryset.exists():
            self.message_user(request, "Select at least one due row for the target month.", level=messages.ERROR)
            return
        target_month = queryset.first().month
        touched = generate_dues_for_month(target_month)
        self.message_user(request, f"Dues ensured for {target_month}. Rows touched: {touched}", level=messages.SUCCESS)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("txn_date", "amount", "txn_uid", "original_txn_id", "source", "imported_at")
    list_filter = ("source",)
    search_fields = ("txn_uid", "original_txn_id", "description")
    ordering = ("-txn_date", "-imported_at")


@admin.register(ExceptionItem)
class ExceptionItemAdmin(admin.ModelAdmin):
    list_display = ("month", "kind", "transaction", "suggested_member", "is_resolved", "created_at")
    list_filter = ("month", "kind", "is_resolved")
    search_fields = ("transaction__txn_uid", "transaction__description", "candidate_member_ids")
    actions = ["mark_resolved"]

    @admin.action(description="Mark selected exceptions as resolved")
    def mark_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True, resolved_at=timezone.now())
        self.message_user(request, f"Marked {updated} exception(s) as resolved.", level=messages.SUCCESS)



