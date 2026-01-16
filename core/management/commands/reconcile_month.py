from __future__ import annotations

from datetime import datetime, date
from django.core.management.base import BaseCommand

from core.services.reconcile import reconcile_month


def parse_month(s: str) -> date:
    dt = datetime.strptime(s.strip(), "%Y-%m")
    return date(dt.year, dt.month, 1)


class Command(BaseCommand):
    help = "Reconcile transactions against dues for a month. Example: python manage.py reconcile_month 2026-01"

    def add_arguments(self, parser):
        parser.add_argument("month", type=str)

    def handle(self, *args, **opts):
        month = parse_month(opts["month"])
        counts = reconcile_month(month)
        self.stdout.write(self.style.SUCCESS(f"Reconcile {month} => {counts}"))
