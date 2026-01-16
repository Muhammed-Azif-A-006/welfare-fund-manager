from __future__ import annotations

from django.core.management.base import BaseCommand
from core.services.importers import import_statement_csv


class Command(BaseCommand):
    help = "Import a statement CSV into transactions. Example: python manage.py import_statement sample_data/statement_demo.csv --source demo"

    def add_arguments(self, parser):
        parser.add_argument("filepath", type=str)
        parser.add_argument("--source", type=str, default="")

        parser.add_argument("--col_txn_id", type=str, default="txn_id")
        parser.add_argument("--col_date", type=str, default="txn_date")
        parser.add_argument("--col_amount", type=str, default="amount")
        parser.add_argument("--col_desc", type=str, default="description")

    def handle(self, *args, **opts):
        n = import_statement_csv(
            filepath=opts["filepath"],
            source=opts["source"],
            col_txn_id=opts["col_txn_id"],
            col_date=opts["col_date"],
            col_amount=opts["col_amount"],
            col_desc=opts["col_desc"],
        )
        self.stdout.write(self.style.SUCCESS(f"Processed {n} rows from {opts['filepath']}"))
