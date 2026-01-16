from __future__ import annotations

from datetime import datetime, date
from django.core.management.base import BaseCommand, CommandError

from core.services.dues import generate_dues_for_month


def parse_month(s: str) -> date:
    # Accept YYYY-MM and convert to YYYY-MM-01
    dt = datetime.strptime(s.strip(), "%Y-%m")
    return date(dt.year, dt.month, 1)


class Command(BaseCommand):
    help = "Generate/update dues for a month. Example: python manage.py generate_dues 2026-01"

    def add_arguments(self, parser):
        parser.add_argument("month", type=str)

    def handle(self, *args, **options):
        month = parse_month(options["month"])
        touched = generate_dues_for_month(month)
        self.stdout.write(self.style.SUCCESS(f"Dues ensured for {month}. Rows touched: {touched}"))
