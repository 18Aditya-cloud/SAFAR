"""Route/voyage risk scoring, explainability, asset failure and SOS triage."""
from datetime import date as Date
from typing import Optional

import numpy as np
import pandas as pd

from ml.config import ASSET_TYPES, LEGS
from ml.features import ASSET_FEATURES, VOYAGE_FEATURES, voyage_frame
from ._ml_store import climatology, load_model

DEFAULTS = {"cargo_t": 40.0, "vessel_age_yr": 14.0, "crew_experience_yr": 8.0}
FACTOR_LABELS = {
    "wind_kts": "High wind", "wave_m": "Rough seas", "sea_ice_conc": "Sea-ice concentration",
    "visibility_km": "Low visibility", "blizzard": "Blizzard conditions", "cargo_t": "Heavy cargo load",
    "vessel_age_yr": "Vessel age", "crew_experience_yr": "Low crew experience", "temp_c": "Temperature",
    "month_sin": "Season", "month_cos": "Season", "leg_code": "Route", "mode_code": "Mode", "planned_days": "Duration",
}


def level_for(score: float) -> str:
    return "LOW" if score < 30 else "MEDIUM" if score < 60 else "HIGH"


def conditions_for(leg_id: str, month: int, overrides: Optional[dict] = None) -> dict:
    """Climatological conditions for a leg/month, optionally overridden with live readings."""
    region = LEGS[leg_id]["region"]
    clim = climatology()
    if clim is not None:
        row = clim.loc[(region, month)]
        cond = {k: float(row[k]) for k in ("temp_c", "wind_kts", "wave_m", "sea_ice_conc", "visibility_km", "blizzard")}
    else:
        cond = {"temp_c": 0, "wind_kts": 20, "wave_m": 2, "sea_ice_conc": 0.2, "visibility_km": 12, "blizzard": 0}
    cond["blizzard"] = 1.0 if cond["blizzard"] >= 0.5 else cond["blizzard"]
    if overrides:
        cond.update({k: v for k, v in overrides.items() if v is not None})
    return cond


def _row(leg_id: str, month: int, cond: dict, extra: dict) -> pd.DataFrame:
    r = {"leg_id": leg_id, "planned_days": LEGS[leg_id]["planned_days"], "month": month, **cond, **DEFAULTS}
    r.update({k: v for k, v in extra.items() if v is not None})
    return voyage_frame(pd.DataFrame([r]))


def _heuristic(cond: dict, leg_id: str) -> dict:
    z = (LEGS[leg_id]["base_risk"] + 0.05 * (cond["wind_kts"] - 20) + 2.0 * cond["sea_ice_conc"]
         + 0.7 * cond["blizzard"] - 0.05 * (cond["visibility_km"] - 12))
    p = float(1 / (1 + np.exp(-(z - 1.0))))
    d = LEGS[leg_id]["planned_days"]
    return {"p_delay": p, "delay_p50": p * d * 0.1, "delay_p90": p * d * 0.4}


def score_route(leg_id: str, month: Optional[int] = None, overrides: Optional[dict] = None,
                cargo_t: Optional[float] = None, vessel_age_yr: Optional[float] = None,
                crew_experience_yr: Optional[float] = None) -> dict:
    if leg_id not in LEGS:
        raise KeyError(f"Unknown leg {leg_id}")
    month = month or Date.today().month
    cond = conditions_for(leg_id, month, overrides)
    extra = {"cargo_t": cargo_t, "vessel_age_yr": vessel_age_yr, "crew_experience_yr": crew_experience_yr}
    planned = LEGS[leg_id]["planned_days"]
    bundle = load_model("voyage_risk")
    factors = []
    if bundle is None:
        h, source = _heuristic(cond, leg_id), "heuristic-fallback"
        p, p50, p90 = h["p_delay"], h["delay_p50"], h["delay_p90"]
    else:
        X = _row(leg_id, month, cond, extra)
        p = float(bundle["clf"].predict_proba(X)[:, 1][0])
        p50 = max(0.0, float(bundle["q50"].predict(X)[0])) * planned
        p90 = max(p50, float(bundle["q90"].predict(X)[0]) * planned)
        source = "gradient-boosting"
        # explainability: swap each driver with its neutral (benign) value and measure the drop in P(delay)
        neutral = {"wind_kts": 15.0, "wave_m": 1.5, "sea_ice_conc": 0.0, "visibility_km": 20.0, "blizzard": 0.0,
                   "cargo_t": 30.0, "vessel_age_yr": 8.0, "crew_experience_yr": 12.0}
        base_inputs = {**cond, **DEFAULTS, **{k: v for k, v in extra.items() if v is not None}}
        for feat, nv in neutral.items():
            X2 = X.copy()
            X2[feat] = nv
            delta = p - float(bundle["clf"].predict_proba(X2)[:, 1][0])
            if delta > 0.01:
                factors.append({"factor": FACTOR_LABELS[feat], "feature": feat, "value": round(float(base_inputs[feat]), 2),
                                "contribution_pct": round(delta * 100, 1)})
        factors.sort(key=lambda f: -f["contribution_pct"])
    score = round(100 * float(np.clip(0.7 * p + 0.3 * min(1.0, p90 / max(planned, 1) / 0.5), 0, 1)), 1)
    return {
        "leg_id": leg_id, "name": LEGS[leg_id]["name"], "mode": LEGS[leg_id]["mode"], "month": month,
        "risk_score": score, "risk_level": level_for(score), "delay_probability": round(p, 3),
        "planned_days": planned, "eta_days_p50": round(planned + p50, 1), "eta_days_p90": round(planned + p90, 1),
        "conditions": {k: round(float(v), 2) for k, v in cond.items()}, "top_factors": factors[:4], "model": source,
    }


def score_all_routes(month: Optional[int] = None, overrides: Optional[dict] = None) -> list:
    return [score_route(k, month, overrides) for k in LEGS]


def route_risk_map(month: Optional[int] = None) -> dict:
    """{route_id: risk_score_0_1} used by the route optimiser."""
    return {r["leg_id"]: r["risk_score"] / 100 for r in score_all_routes(month)}


# ------------------------------------------------------------------ assets
def score_asset(asset_type: str, telemetry: Optional[dict] = None) -> dict:
    bundle = load_model("asset_failure")
    atype = asset_type.upper() if asset_type.upper() in ASSET_TYPES else "VEHICLE"
    if bundle is None:
        return {"failure_probability_30d": None, "risk_score": None, "model": "unavailable"}
    tel = dict(bundle["type_medians"][atype])
    tel.update({k: v for k, v in (telemetry or {}).items() if v is not None})
    tel["type_code"] = ASSET_TYPES.index(atype)
    X = pd.DataFrame([tel])[ASSET_FEATURES]
    p = float(bundle["clf"].predict_proba(X)[:, 1][0])
    return {"failure_probability_30d": round(p, 3), "risk_score": round(p * 100, 1), "risk_level": level_for(p * 100),
            "telemetry_used": {k: tel[k] for k in ASSET_FEATURES[1:]},
            "note": "Uses fleet-median telemetry for missing fields." if not telemetry else "Uses supplied telemetry.",
            "model": "random-forest"}


# ------------------------------------------------------------------ SOS triage
SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
RESPONSE_PLAYBOOK = {
    "MEDICAL_EMERGENCY": "Dispatch medical unit and doctor; prepare medevac request; check medical kit stock.",
    "FIRE": "Activate fire response, isolate power/fuel, evacuate affected module.",
    "VEHICLE_FAILURE": "Send recovery vehicle; check spare-part stock; ensure crew shelter and comms.",
    "CREVASSE_ACCIDENT": "Launch rescue team with rope kit; mark hazard on route map; avoid the corridor.",
    "POWER_FAILURE": "Switch to backup generator; shed non-critical loads; monitor diesel days-left.",
    "WEATHER_ENTRAPMENT": "Hold movement; confirm shelter supplies; schedule recovery in weather window.",
    "FUEL_LEAK": "Isolate source, contain spill, remove ignition sources, reconcile fuel inventory.",
    "COMMUNICATION_LOSS": "Try backup channels; dispatch check-in team if silence exceeds safe window.",
    "SUPPLY_SHORTAGE": "Reprioritise cargo for next sailing; apply rationing plan to protect reserves.",
}


def triage_sos(text: str) -> dict:
    bundle = load_model("sos_triage")
    if bundle is None:
        return {"incident_type": "UNKNOWN", "severity": "HIGH", "confidence": None, "model": "unavailable"}
    it, sv = bundle["incident_type"], bundle["severity"]
    itype = it.predict([text])[0]
    sev_proba = sv.predict_proba([text])[0]
    sev = sv.classes_[int(np.argmax(sev_proba))]
    return {"incident_type": itype, "severity": sev, "confidence": round(float(sev_proba.max()), 3),
            "type_confidence": round(float(it.predict_proba([text])[0].max()), 3),
            "recommended_response": RESPONSE_PLAYBOOK.get(itype, "Escalate to station leader."),
            "model": "tfidf-logreg"}
