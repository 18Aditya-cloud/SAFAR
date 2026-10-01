# SAFAR AI/ML module

Everything runs **offline** (scikit-learn + SciPy, models are small `.joblib` files). No internet or GPU needed.

## Modules

| # | Capability | Method | Code | API |
|---|---|---|---|---|
| 1 | Route/voyage risk score + explanation | Gradient boosting classifier; drivers by counterfactual ("what if this factor were benign") | `services/risk_engine.py` | `GET /api/risks/routes`, `POST /api/risks/score` |
| 2 | ETA prediction with ranges | Quantile gradient boosting (P50/P90 of delay) | `risk_engine.py` | same (`eta_days_p50/p90`) |
| 3 | Inventory depletion forecast | GB consumption model calibrated to site rate + Monte Carlo bands | `services/inventory_engine.py` | `GET /api/risks/inventory` |
| 4 | Consumption anomaly detection | Residual z-score vs model | `inventory_engine.py` | `POST /api/risks/inventory/anomaly` |
| 5 | Cargo optimisation | 0/1 multi-constraint knapsack (SciPy MILP/HiGHS), critical items forced, deadline vs P90 ETA | `services/cargo_optimizer.py` | `POST /api/optimization/cargo` |
| 6 | Route optimisation | Risk-weighted path search on GeoJSON graph, time vs safety alternatives | `services/route_engine.py` | `GET /api/optimization/routes` |
| 7 | What-if simulation | Monte Carlo over resupply delay, stock loss, consumption spikes | `services/simulation_engine.py` | `POST /api/simulate`, `POST /api/digital-twin/what-if` |
| 8 | Digital twin + readiness score | Aggregates 1-7 with DB state | `services/digital_twin.py` | `GET /api/digital-twin` |
| 9 | Asset failure prediction | Random forest on telemetry | `risk_engine.score_asset` | `GET /api/risks/assets` |
| 10 | SOS triage | TF-IDF + logistic regression (type, severity) + response playbook | `risk_engine.triage_sos` | `POST /api/risks/triage` |
| 11 | Offline sync + model manifest | Severity-ordered SOS queue, checksummed model files | `services/sync_engine.py` | `GET /api/sync/status`, `POST /api/sync/flush`, `GET /api/sync/models` |
| 12 | Reports / model metrics | Latest evaluation | `routers/reports.py` | `GET /api/reports/summary`, `/model-metrics` |

## Run

```bash
cd backend
pip install -r requirements.txt
python -m ml.generate_synthetic     # optional: regenerate datasets
python -m ml.train                  # optional: retrain (models are already committed)
pytest -q
uvicorn app.main:app --reload --port 8000
```

## Evaluation (synthetic data, time-based split)

Voyage delay AUC 0.91, P90 coverage 0.85; consumption MAPE about 5%; anomaly recall about 1.0; asset failure AUC 0.79; SOS severity accuracy 0.96.
These numbers show the pipeline works. They are **not** claims of real-world accuracy because the data is synthetic.

## Limitations to state in the submission
- Data is synthetic; swap in real NCPOR / IMD / NSIDC / ERA5 records for real validation.
- Conditions used at inference are monthly climatology unless live readings are passed to `/api/risks/score`.
- SOS transmission is simulated; a real channel (satellite/HF) is needed.
