"""Shared configuration for SAFAR AI/ML (paths, legs, vessel, seeds)."""
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent
DATA_DIR = ML_DIR / "data"
MODELS_DIR = ML_DIR / "models"
SEED = 42

# Transport legs (ids match app/data/routes.geojson)
LEGS = {
    "R001": {"name": "Goa to Mumbai", "mode": "VOYAGE", "region": "INDIAN_OCEAN", "planned_days": 2, "base_risk": -0.8},
    "R002": {"name": "Mumbai to Cape Town", "mode": "VOYAGE", "region": "INDIAN_OCEAN", "planned_days": 18, "base_risk": -0.2},
    "R003": {"name": "Cape Town to Maitri", "mode": "VOYAGE", "region": "SOUTHERN_OCEAN", "planned_days": 12, "base_risk": 0.6},
    "R004": {"name": "Cape Town to Antarctica (air)", "mode": "AIR", "region": "SOUTHERN_OCEAN", "planned_days": 2, "base_risk": 0.5},
    "R005": {"name": "Maitri to Bharati (field)", "mode": "FIELD", "region": "ANTARCTIC", "planned_days": 3, "base_risk": 0.2},
}
MODE_CODE = {"VOYAGE": 0, "AIR": 1, "FIELD": 2}
LEG_CODE = {k: i for i, k in enumerate(LEGS)}
REGIONS = ["INDIAN_OCEAN", "SOUTHERN_OCEAN", "ANTARCTIC"]

# Default vessel for cargo optimisation (demo values)
VESSEL = {"name": "Polar supply vessel", "capacity_kg": 45000.0, "capacity_m3": 300.0}

PRIORITY_WEIGHT = {"CRITICAL": 1000.0, "HIGH": 100.0, "NORMAL": 20.0, "LOW": 5.0}
INVENTORY_ITEMS = ["Food Supplies", "Diesel Fuel", "Medical Kits", "Spare Parts"]
ASSET_TYPES = ["VEHICLE", "GENERATOR", "MEDICAL", "COMMS"]
