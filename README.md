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

4. Migrations run automatically when the API starts (`python main.py api serve`).
   You can still apply them manually:

```bash
python main.py db upgrade
```

5. Test SAP Fiori login and navigation (Document Date = Today):

```bash
python main.py sap test --visible --keep-open 10
```

6. Run invitation extraction:

```bash
# Document Date = Today (default)
python main.py extract invitations --visible --mode today

# Document Date = Yesterday
python main.py extract invitations --visible --mode yesterday

# No date filter — Go only
python main.py extract invitations --visible --mode all
```

7. Start the API server:

```bash
python main.py api serve
```

8. Run other extraction jobs:

```bash
python main.py extract invitations
python main.py extract cases
```

## API

| Endpoint | Mode |
|----------|------|
| `GET /api/invitations/today` | Document Date = Today |
| `GET /api/invitations/yesterday` | Document Date = Yesterday |
| `GET /api/invitations/all` | No date filter (Go only) |

Optional query param on each: `invitationId` (e.g. `UAE1401324`).

```bash
python main.py api serve

curl http://127.0.0.1:8000/api/invitations/today
curl http://127.0.0.1:8000/api/invitations/yesterday
curl http://127.0.0.1:8000/api/invitations/all
curl "http://127.0.0.1:8000/api/invitations/today?invitationId=UAE1401324"
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

- `app/controllers/invitation_controllers/` — invitation extraction service, scraper, repository
- `app/controllers/selenuim_client.py` — shared SAP Selenium client
- `app/configs/` — settings, logging, SAP auth helpers
- `app/clients/` — database client, SAP selectors
- `app/models/` — SQLAlchemy ORM models
- `app/schemas/` — Pydantic validation schemas
- `alembic/` — database migrations

## Status

- [x] Step 1 — Project foundation
- [x] Step 2 — Database layer
- [x] Step 3 — SAP client skeleton
- [x] Step 4 — Invitation extraction
- [ ] Step 5 — Case + RFQ extraction
