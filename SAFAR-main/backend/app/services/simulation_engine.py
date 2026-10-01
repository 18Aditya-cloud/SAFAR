"""Monte Carlo what-if scenario engine (replaces the hard-coded impact table)."""
from typing import Optional

import numpy as np

from .inventory_engine import HORIZON, depletion_samples
from .risk_engine import score_route

# stock_loss: fraction of stock lost immediately; mult: consumption multiplier; delay: extra resupply delay (days, mean, sd)
SCENARIOS = {
    "Cargo delay": {"delay": (10, 4), "mult": {}, "stock_loss": {}},
    "Vehicle failure": {"delay": (3, 2), "mult": {"Spare Parts": 2.0, "Diesel Fuel": 1.1}, "stock_loss": {}},
    "Fuel shortage": {"delay": (0, 0), "mult": {}, "stock_loss": {"Diesel Fuel": 0.4}},
    "Food shortage": {"delay": (0, 0), "mult": {}, "stock_loss": {"Food Supplies": 0.35}},
    "Severe weather": {"delay": (9, 4), "mult": {"Diesel Fuel": 1.35, "Food Supplies": 1.1}, "stock_loss": {}},
    "Medical emergency": {"delay": (0, 0), "mult": {"Medical Kits": 6.0}, "stock_loss": {}},
}
DEFAULT_SCENARIO = {"delay": (5, 3), "mult": {}, "stock_loss": {}}


def _level(p: float) -> str:
    return "LOW" if p < 0.15 else "MEDIUM" if p < 0.5 else "HIGH"


def _resupply_samples(rng, n, resupply_in_days, extra_delay, leg_id="R003", month=None):
    """Resupply arrival day = planned + weather/route delay (from ML P50/P90) + scenario delay."""
    r = score_route(leg_id, month)
    p50, p90 = r["eta_days_p50"] - r["planned_days"], r["eta_days_p90"] - r["planned_days"]
    sigma = max(0.05, (np.log(max(p90, 0.2)) - np.log(max(p50, 0.1))) / 1.2816)
    route_delay = rng.lognormal(np.log(max(p50, 0.1)), sigma, n)
    scen = np.maximum(rng.normal(extra_delay[0], max(extra_delay[1], 1e-6), n), 0) if extra_delay[0] > 0 else 0
    return resupply_in_days + route_delay + scen


def run(scenario: str, inventory: list, personnel: int = 60, resupply_in_days: float = 30.0, n_sims: int = 800,
        month: Optional[int] = None, seed: int = 11) -> dict:
    """inventory: dicts {item, quantity, daily_consumption, critical_days}."""
    spec = SCENARIOS.get(scenario, DEFAULT_SCENARIO)
    rng = np.random.default_rng(seed)
    resupply_before = _resupply_samples(rng, n_sims, resupply_in_days, (0, 0), month=month)
    resupply_after = _resupply_samples(rng, n_sims, resupply_in_days, spec["delay"], month=month)
    items = []
    for row in inventory:
        name = row["item"]
        b = depletion_samples(name, row["quantity"], row["daily_consumption"], personnel, n_sims=n_sims)
        a = depletion_samples(name, row["quantity"] * (1 - spec["stock_loss"].get(name, 0)), row["daily_consumption"], personnel,
                              multiplier=spec["mult"].get(name, 1.0), n_sims=n_sims, seed=8)
        if b is None or a is None:
            continue
        sb, sa = b[0], a[0]
        p_before, p_after = float((sb < resupply_before).mean()), float((sa < resupply_after).mean())
        gap_before = float(np.maximum(resupply_before - sb, 0).mean())  # expected days without stock before resupply
        gap_after = float(np.maximum(resupply_after - sa, 0).mean())
        items.append({
            "item": name, "prob_stockout_before": round(p_before, 3), "prob_stockout_after": round(p_after, 3),
            "shortfall_days_before": round(gap_before, 1), "shortfall_days_after": round(gap_after, 1),
            "days_left_p50_before": round(float(np.median(sb)), 1), "days_left_p50_after": round(float(np.median(sa)), 1),
            "days_left_p10_after": round(float(np.percentile(sa, 10)), 1), "critical_days": row.get("critical_days", 7),
        })
    if not items:
        return {"scenario": scenario, "impact_score": 0, "risk_before": "LOW", "risk_after": "LOW", "items": [],
                "recommendation": "Models not trained: run `python -m ml.train`.", "model": "unavailable"}
    inc = np.array([i["prob_stockout_after"] - i["prob_stockout_before"] for i in items])
    gap = np.array([i["shortfall_days_after"] - i["shortfall_days_before"] for i in items])
    # impact blends the rise in stock-out probability with the extra days spent without stock (saturating at ~20 d)
    impact = round(float(100 * np.clip(0.5 * inc.max() + 0.5 * (1 - np.exp(-max(gap.max(), 0) / 8)), 0, 1)), 1)
    pb, pa = max(i["prob_stockout_before"] for i in items), max(i["prob_stockout_after"] for i in items)
    return {
        "scenario": scenario, "impact_score": max(impact, 0.0), "risk_before": _level(pb), "risk_after": _level(pa),
        "resupply_before_p50_days": round(float(np.median(resupply_before)), 1),
        "resupply_after_p50_days": round(float(np.median(resupply_after)), 1),
        "items": sorted(items, key=lambda i: -i["prob_stockout_after"]), "recommendation": recommend(scenario, items, spec),
        "n_simulations": n_sims, "model": "monte-carlo",
    }


def recommend(scenario: str, items: list, spec: dict) -> str:
    at_risk = [i for i in items if i["prob_stockout_after"] >= 0.3]
    if not at_risk:
        return f"'{scenario}': reserves absorb this scenario (no item above 30% stock-out probability). Monitor and keep routes updated."
    parts = []
    for i in sorted(at_risk, key=lambda x: -x["prob_stockout_after"])[:3]:
        base = " (already at risk before this scenario)" if i["prob_stockout_before"] >= 0.3 else ""
        parts.append(f"{i['item']}: {round(i['prob_stockout_after'] * 100)}% stock-out chance, "
                     f"~{i['shortfall_days_after']} d without stock before resupply{base}")
    actions = ["Protect emergency reserves and apply rationing to at-risk items",
               "Re-run cargo optimisation so at-risk items are CRITICAL priority on the next sailing"]
    if spec["delay"][0] > 0:
        actions.append("Consider air-lift from Cape Town (R004) for the critical items")
    return "; ".join(parts) + ". Actions: " + "; ".join(actions) + "."
