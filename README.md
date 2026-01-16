# Welfare Fund Manager (Django Admin MVP)

Automated member fund collection support for welfare societies:
- Generate monthly dues with reference codes (e.g., M007-202601)
- Import bank/UPI statement CSV
- Auto-reconcile payments
- Exceptions Inbox: Review / Unmapped / Duplicate
- Admin confirms edge cases

## Tech
- Django + SQLite (Admin-first UI)
- CSV import + deterministic transaction hashing for dedupe

## Data Model
- Member(member_id, monthly_amount, ...)
- Due(month, member, reference_code, status, matched_transaction)
- Transaction(txn_uid hash, date, amount, description)
- ExceptionItem(kind: REVIEW/UNMAPPED/DUPLICATE)

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver



## Clean requirements
Your `requirements.txt` should at minimum include:
- Django
- (optional) pandas if you used it; current code uses csv module so it’s not required.

To regenerate cleanly:
```bash
pip freeze > requirements.txt
