# SAFAR synthetic datasets

All files are **synthetic** (seeded, reproducible: `python -m ml.generate_synthetic`, seed 42).
Seasonality follows austral summer (Nov-Mar operating window); values are plausible, not real records.

| File | Rows | Used for | Key columns |
|---|---|---|---|
| `weather_conditions.csv` | 5,478 | climatology + voyage features | date, region (INDIAN_OCEAN / SOUTHERN_OCEAN / ANTARCTIC), temp_c, wind_kts, wave_m, sea_ice_conc, visibility_km, blizzard |
| `voyage_history.csv` | 3,200 | delay probability + ETA P50/P90 models | leg_id (R001-R005), depart_date, planned_days, cargo_t, vessel_age_yr, crew_experience_yr, weather at departure, delay_days, delayed, incident |
| `inventory_consumption.csv` | 7,304 | consumption forecast + anomaly detection | date, item (Food/Diesel/Medical/Spare Parts), personnel, temp_c, consumption, is_anomaly |
| `asset_telemetry.csv` | 960 | predictive maintenance | asset_id, asset_type, age_yr, operating_hours_30d, vibration_mm_s, oil_pressure_dev, days_since_maintenance, load_factor, fault_next_30d |
| `sos_reports.csv` | 900 | SOS text triage (type + severity) | text, incident_type (9 classes), severity (LOW..CRITICAL, ~4% label noise) |
| `cargo_manifest.csv` | 60 | cargo optimiser demo | cargo_code, category, weight_kg, volume_m3, priority, deadline_days, destination |

Replace with real NCPOR/IMD/NSIDC/ERA5 data by keeping the same column names and re-running `python -m ml.train`.
