# SAFAR — Smart Antarctic Expedition & Resource Management

Offline-first SIH MVP scaffold.

## Stack
- Frontend: React + Vite + Tailwind CSS + Leaflet
- Backend: FastAPI + SQLAlchemy + Pydantic
- Database: SQLite
- Intelligence placeholders: inventory prediction, risk, optimization, simulation, SOS
- Maps: local GeoJSON (`frontend/public/data/polar.geojson`)

## Run backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Run frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173
Backend docs: http://localhost:8000/docs

## Offline concept
The core APIs, SQLite database, GeoJSON map and decision-support endpoints run locally.
Remote SOS transmission is intentionally represented as a queue/sync operation; actual transmission requires an available communication channel.
