# Mock Database Seed

This folder contains PostgreSQL mock data for the current Django `CarePlan` model.

## Import with TablePlus

1. Start PostgreSQL and run Django migrations first:

```bash
python manage.py migrate
```

2. Open your PostgreSQL database in TablePlus.
3. Open `mock_data/seed_careplan_postgres.sql`.
4. Run the whole file.
5. Confirm data with:

```sql
SELECT COUNT(*) FROM careplans_careplan;
```

Expected counts:

| table | count |
|---|---:|
| careplans_careplan | 5 |

## Regenerate

```bash
python scripts/generate_mock_seed.py
```

The seed is intentionally idempotent for a mock database: it truncates `careplans_careplan` before inserting fresh rows.
