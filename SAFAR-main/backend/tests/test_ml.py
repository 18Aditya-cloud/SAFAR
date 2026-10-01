"""Run from backend/:  pytest -q"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ml.config import MODELS_DIR  # noqa: E402

if not (MODELS_DIR / "voyage_risk.joblib").exists():
    from ml import generate_synthetic, train
    generate_synthetic.main()
    train.main()

from app.services import risk_engine, inventory_engine, cargo_optimizer, simulation_engine, route_engine  # noqa: E402


def test_polar_summer_is_riskier_than_indian_ocean():
    assert risk_engine.score_route("R003", 1)["risk_score"] > risk_engine.score_route("R001", 1)["risk_score"]


def test_winter_southern_ocean_is_high_risk():
    assert risk_engine.score_route("R003", 7)["risk_level"] == "HIGH"


def test_eta_quantiles_ordered():
    r = risk_engine.score_route("R003", 1)
    assert r["planned_days"] <= r["eta_days_p50"] <= r["eta_days_p90"]


def test_worse_weather_raises_risk():
    calm = risk_engine.score_route("R003", 1, {"wind_kts": 10, "sea_ice_conc": 0.05})["risk_score"]
    storm = risk_engine.score_route("R003", 1, {"wind_kts": 55, "sea_ice_conc": 0.6, "blizzard": 1})["risk_score"]
    assert storm > calm


def test_triage_critical():
    t = risk_engine.triage_sos("vehicle fell into crevasse, crew trapped inside")
    assert t["incident_type"] == "CREVASSE_ACCIDENT" and t["severity"] in ("CRITICAL", "HIGH")


def test_inventory_forecast_monotonic_with_stock():
    a = inventory_engine.forecast_item("Food Supplies", 1000, 100, 7)["days_left"]
    b = inventory_engine.forecast_item("Food Supplies", 3000, 100, 7)["days_left"]
    assert b > a


def test_inventory_anomaly():
    assert inventory_engine.detect_anomaly("Diesel Fuel", 900, 60, 1)["anomaly"]
    assert not inventory_engine.detect_anomaly("Diesel Fuel", 250, 60, 1)["anomaly"]


def test_cargo_respects_capacity_and_loads_critical():
    items = [{"cargo_code": f"C{i}", "weight_kg": 1000, "volume_m3": 3, "priority": p, "deadline_days": 60}
             for i, p in enumerate(["CRITICAL"] * 5 + ["LOW"] * 60)]
    r = cargo_optimizer.optimise_cargo(items, capacity_kg=20000, capacity_m3=100)
    assert r["utilisation"]["weight_kg"] <= 20000
    assert r["loaded_by_priority"]["CRITICAL"] == 5


def test_cargo_deadline_deferral():
    items = [{"cargo_code": "X", "weight_kg": 10, "priority": "HIGH", "deadline_days": 5}]
    r = cargo_optimizer.optimise_cargo(items, eta_days=14)
    assert r["deferred"] and not r["selected"]


def test_simulation_worse_after_scenario():
    inv = [{"item": "Food Supplies", "quantity": 4000, "daily_consumption": 110, "critical_days": 7},
           {"item": "Diesel Fuel", "quantity": 9000, "daily_consumption": 260, "critical_days": 7}]
    r = simulation_engine.run("Food shortage", inv, n_sims=300)
    food = next(i for i in r["items"] if i["item"] == "Food Supplies")
    assert food["prob_stockout_after"] >= food["prob_stockout_before"]


def test_haversine_known_distance():
    # Cape Town to Goa approx 8,100 km great-circle
    d = route_engine.haversine_distance(-33.92, 18.42, 15.49, 73.83)
    assert 7500 < d < 9500


def test_route_alternatives():
    rm = risk_engine.route_risk_map(1)
    res = route_engine.find_routes("Cape Town", "Maitri", rm)
    assert len(res) == 2 and res[0]["rank"] == 1
