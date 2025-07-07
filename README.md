# Stat-Arb Pairs Trader

This is a minimal pairs trading application built with FastAPI. Historical and live market data comes from [Polygon.io](https://polygon.io). Execution is simulated only.

## Quick Start

```bash
export POLYGON_API_KEY="pk_your_key"  # optional for back-tests, required for live mode
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn trader.main:app --reload
```

Open `http://localhost:8000/docs` for the API. Back-tests work without an API key using `yfinance` data. Live mode requires `POLYGON_API_KEY`.
