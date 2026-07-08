# Al Ghanem SAP Data Extraction

Phase 1 ETL: pull Sales Enquiry (invitations) and Case Registration data from SAP S/4HANA Cloud (Fiori) into a local PostgreSQL database.

## Setup

1. Copy the environment template and fill in your values:

```bash
cp .env-example .env
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create the local database (example):

```sql
CREATE DATABASE al_ghanem_extraction;
```

4. Apply migrations:

```bash
python main.py db upgrade
```

5. Test SAP Fiori login and navigation:

```bash
python main.py sap test --visible --keep-open 10
```

6. Run invitation extraction:

```bash
python main.py extract invitations --visible --from-date 2026-01-01 --to-date 2026-01-31
```

7. Run other extraction jobs:

```bash
python main.py extract invitations
python main.py extract cases
```

## Database schema

### `invitations` (Phase 1 — finalized)

| Column | Type | Description |
|--------|------|-------------|
| `inv_ref` | string (PK) | Invitation Reference — linking key |
| `customer_ref` | string | Customer reference number |
| `customer_name` | string | Customer name |
| `scope_of_work` | text | Scope of work description |
| `inv_subject` | string | Invitation subject / title |
| `product_type` | string | Product type |
| `closing_date` | date | Invitation closing date |
| `extracted_at` | timestamptz | First extraction timestamp |
| `updated_at` | timestamptz | Last update timestamp |

### `cases` (Task 2 — fields TBD)

Stores case overview data in `overview_data` (JSONB) until the SAP Overview page field list is finalized. Linked via `inv_ref`.

### `rfq_items` (Task 2 — fields TBD)

Stores RFQ line items in `item_data` (JSONB) until the external items field list is finalized. Linked via `inv_ref` and `case_id`.

## Project layout

- `app/configs/` — settings, logging, SAP auth helpers
- `app/clients/` — database client, repositories
- `app/models/` — SQLAlchemy ORM models
- `app/schemas/` — Pydantic validation schemas
- `app/controllers/` — extraction business logic (Step 4+)
- `alembic/` — database migrations

## Status

- [x] Step 1 — Project foundation
- [x] Step 2 — Database layer
- [x] Step 3 — SAP client skeleton
- [x] Step 4 — Invitation extraction
- [ ] Step 5 — Case + RFQ extraction
