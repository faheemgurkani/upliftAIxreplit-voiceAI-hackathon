# Tests

## Backend pipeline (call → dashboard)

Run from `gawah-backend/` with the project venv:

```bash
# Full-spec tools → engines → dashboard/clusters/KPIs
PYTHONUNBUFFERED=1 ../.venv/bin/python scripts/smoke_test.py

# Data streaming paths (tool / phone / web) into the dashboard
PYTHONUNBUFFERED=1 ../.venv/bin/python scripts/pipeline_stream_test.py
```

Both scripts use isolated JSON stores (`data/smoke_store.json`, `data/pipeline_stream_store.json`) so demo seed data is not required.

Suggested layout as the suite grows:

- `tests/unit/`
- `tests/integration/`
- `tests/e2e/`
