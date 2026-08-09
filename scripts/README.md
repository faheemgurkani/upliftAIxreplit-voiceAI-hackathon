# Scripts

Cross-platform helpers for setup and local demo.

## Setup & run (preferred)

| File | Platform |
|------|----------|
| [`setup.py`](./setup.py) | All (source of truth) |
| [`setup.sh`](./setup.sh) | macOS / Linux |
| [`setup.ps1`](./setup.ps1) | Windows PowerShell |
| [`setup.cmd`](./setup.cmd) | Windows CMD |

```bash
# install deps + env + demo seed
python scripts/setup.py install

# API :8000 + UI :5173
python scripts/setup.py dev

python scripts/setup.py check
python scripts/setup.py seed
```

Full teammate guide: [`../docs/LOCAL_SETUP.md`](../docs/LOCAL_SETUP.md).

## Other

| Script | Purpose |
|--------|---------|
| [`check-env.sh`](./check-env.sh) | Quick “does root `.env` exist?” |
| `gawah-backend/scripts/seed_demo.py` | Demo statements / clusters / calls (`NBRA7K`, `SHPK2M`, `NBRC9Q`) |
| `gawah-backend/scripts/smoke_test.py` | Backend smoke (isolated store) |
| `gawah-backend/scripts/live_integration_test.py` | Live Uplift TTS / assistant probes |

Root overview: [`../README.md`](../README.md).
