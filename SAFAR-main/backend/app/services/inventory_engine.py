"""Inventory depletion forecasting with uncertainty bands + anomaly detection."""
from datetime import date as Date, timedelta
from typing import Iterable, Optional

import numpy as np
import pandas as pd

from ml.features import INVENTORY_FEATURES
from ._ml_store import climatology, load_model

HORIZON = 365


def _temp_for(month: int) -> float:
    clim = climatology()
    return float(clim.loc[("ANTARCTIC", month)]["temp_c"]) if clim is not None else -10.0


def _daily_rates(item: str, personnel: int, start: Date, days: int, multiplier: float = 1.0):
    bundle = load_model("inventory_forecast")
    dates = [start + timedelta(days=i) for i in range(days)]
    if bundle is None or item not in bundle["items"]:
        return dates, None, None
    X = pd.DataFrame({
        "personnel": personnel, "temp_c": [_temp_for(d.month) for d in dates],
        "month_sin": [np.sin(2 * np.pi * d.month / 12) for d in dates],
        "month_cos": [np.cos(2 * np.pi * d.month / 12) for d in dates],
    })[INVENTORY_FEATURES]
    m = bundle["items"][item]
    return dates, np.maximum(m["model"].predict(X), 1e-6) * multiplier, m["rel_sigma"]


def depletion_samples(item: str, quantity: float, daily_consumption: float, personnel: int = 60,
                      start: Optional[Date] = None, multiplier: float = 1.0, n_sims: int = 400, seed: int = 7):
    """Monte Carlo days-to-stockout samples (HORIZON+1 = not within horizon). Returns (samples, calib, mean_days) or None."""
    start = start or Date.today()
    dates, rate, sigma = _daily_rates(item, personnel, start, HORIZON, multiplier)
    if rate is None:
        return None
    calib = (daily_consumption / (rate[0] / multiplier)) if daily_consumption > 0 else 1.0
    rate = rate * calib
    rng = np.random.default_rng(seed)
    noise = rng.normal(1.0, sigma, size=(n_sims, len(rate)))
    level = rng.lognormal(0.0, 0.10, size=(n_sims, 1))  # persistent uncertainty (headcount, rationing, miscount)
    cum = np.cumsum(rate[None, :] * np.maximum(noise, 0.2) * level, axis=1)
    exhausted = cum >= quantity
    idx = np.where(exhausted.any(axis=1), exhausted.argmax(axis=1) + 1, HORIZON + 1)
    cum_mean = np.cumsum(rate)
    mean_days = float(np.searchsorted(cum_mean, quantity) + 1) if cum_mean[-1] >= quantity else float(HORIZON + 1)
    return idx.astype(float), float(calib), mean_days


def forecast_item(item: str, quantity: float, daily_consumption: float, critical_days: float,
                  personnel: int = 60, start: Optional[Date] = None, multiplier: float = 1.0) -> dict:
    """Forecast stock-out date. The ML rate curve is calibrated to the site's recorded daily rate."""
    start = start or Date.today()
    naive_days = quantity / daily_consumption if daily_consumption > 0 else 999.0
    res = depletion_samples(item, quantity, daily_consumption, personnel, start, multiplier)
    if res is None:  # fallback when models are not trained
        d = naive_days / max(multiplier, 1e-6)
        return {"item": item, "days_left": round(d, 1), "days_left_p10": round(d * 0.85, 1), "days_left_p90": round(d * 1.15, 1),
                "stockout_date": str(start + timedelta(days=int(min(d, 3650)))), "model": "linear-fallback",
                "status": "CRITICAL" if d <= critical_days else "SAFE"}
    idx, calib, mean_days = res
    d10, d50, d90 = np.percentile(idx, [10, 50, 90])
    return {
        "item": item, "days_left": round(mean_days, 1), "days_left_p10": round(float(d10), 1), "days_left_p90": round(float(d90), 1),
        "stockout_date": None if mean_days > HORIZON else str(start + timedelta(days=int(mean_days))),
        "naive_days_left": round(naive_days, 1), "site_calibration": round(calib, 3),
        "status": "CRITICAL" if float(d10) <= critical_days else "WATCH" if mean_days <= 2 * critical_days else "SAFE",
        "model": "gradient-boosting+monte-carlo",
    }


def forecast_inventory(rows: Iterable, personnel: int = 60, multiplier: float = 1.0) -> list:
    out = []
    for r in rows:
        f = forecast_item(r.item, r.quantity, r.daily_consumption, r.critical_days, personnel, multiplier=multiplier)
        f.update({"category": r.category, "quantity": r.quantity, "unit": r.unit, "location": r.location})
        out.append(f)
    return out


def detect_anomaly(item: str, observed: float, personnel: int, month: int) -> dict:
    """Flag consumption far above what the model expects (leak, theft, spoilage, miscount)."""
    bundle = load_model("inventory_forecast")
    if bundle is None or item not in bundle["items"]:
        return {"anomaly": False, "model": "unavailable"}
    X = pd.DataFrame([{"personnel": personnel, "temp_c": _temp_for(month),
                       "month_sin": np.sin(2 * np.pi * month / 12), "month_cos": np.cos(2 * np.pi * month / 12)}])[INVENTORY_FEATURES]
    m = bundle["items"][item]
    exp = float(m["model"].predict(X)[0])
    z = (observed - exp) / exp / m["rel_sigma"]
    return {"item": item, "expected": round(exp, 2), "observed": observed, "z_score": round(float(z), 2), "anomaly": bool(z > 3.5),
            "model": "residual-zscore"}
