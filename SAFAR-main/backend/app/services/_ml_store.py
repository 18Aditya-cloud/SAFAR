"""Lazy loader for trained models + climatology (fully offline)."""
import json
from functools import lru_cache

import joblib
import pandas as pd

from ml.config import DATA_DIR, MODELS_DIR


@lru_cache(maxsize=None)
def load_model(name: str):
    path = MODELS_DIR / f"{name}.joblib"
    if not path.exists():
        return None
    return joblib.load(path)


@lru_cache(maxsize=1)
def climatology():
    """Monthly mean conditions per region from the weather dataset (offline climatology)."""
    path = DATA_DIR / "weather_conditions.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, parse_dates=["date"])
    df["month"] = df["date"].dt.month
    return df.groupby(["region", "month"]).mean(numeric_only=True).round(2)


def metrics():
    path = MODELS_DIR / "metrics.json"
    return json.loads(path.read_text()) if path.exists() else {}


def models_ready() -> bool:
    return all(load_model(n) is not None for n in ("voyage_risk", "inventory_forecast", "asset_failure", "sos_triage"))
