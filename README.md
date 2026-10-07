# TrustLock — Verify the Action

TrustLock is a multimodal risk analysis and dynamic challenge framework. It operates on a deterministic pipeline that evaluates context, intent, and evidence simultaneously. Based on a calculated Trust Score, it can automatically ALLOW, BLOCK, or trigger a VERIFY challenge (a live voice/speech challenge) to confirm user intent.

## Tech Stack
- **Backend:** Python, FastAPI, SQLite (hash-chained ledger)
- **Frontend:** React, Vite, Plain CSS (Tokens-based design system, no UI libraries)

## How to Run
To run both the backend and frontend simultaneously, execute the demo script:
```powershell
.\start-demo.ps1
```

## Running Tests
To run the backend test suite:
```powershell
cd backend
uv run pytest
```

To verify the frontend build:
```powershell
cd frontend
npm run build
```