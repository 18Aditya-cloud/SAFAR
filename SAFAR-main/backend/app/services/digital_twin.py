"""Digital twin: live model of stations, stock, assets, routes and incidents."""
from typing import Optional

from sqlalchemy.orm import Session

from ..models import Asset, Expedition, Inventory, SOSEvent
from . import risk_engine, simulation_engine
from .inventory_engine import forecast_inventory

STATUS_PENALTY = {"CRITICAL": 25, "WATCH": 8, "SAFE": 0}


def _personnel(db: Session, default: int = 60) -> int:
    total = sum(e.personnel_count or 0 for e in db.query(Expedition).filter(Expedition.status == "ACTIVE").all())
    return total or default


def build_twin(db: Session, month: Optional[int] = None) -> dict:
    personnel = _personnel(db)
    inv = forecast_inventory(db.query(Inventory).all(), personnel=personnel)
    routes = risk_engine.score_all_routes(month)
    assets = []
    for a in db.query(Asset).all():
        ml = risk_engine.score_asset(a.asset_type)
        assets.append({"id": a.id, "name": a.name, "type": a.asset_type, "status": a.status, "location": a.location,
                       "recorded_risk": a.risk_score, "predicted_failure_30d": ml.get("failure_probability_30d"),
                       "ml_risk_level": ml.get("risk_level")})
    sos = []
    for s in db.query(SOSEvent).filter(SOSEvent.status != "RESOLVED").all():
        t = risk_engine.triage_sos(s.description or s.incident_type)
        sos.append({"id": s.id, "incident_type": s.incident_type, "status": s.status, "triage": t})
    # readiness: start at 100, subtract for stock, route and asset stress
    penalty = sum(STATUS_PENALTY.get(i["status"], 0) for i in inv)
    penalty += 0.15 * max((r["risk_score"] for r in routes), default=0)
    penalty += sum(6 for a in assets if (a["predicted_failure_30d"] or 0) >= 0.5)
    penalty += sum({"CRITICAL": 10, "HIGH": 6}.get(x["triage"].get("severity"), 2) for x in sos)
    readiness = round(max(0.0, 100 - penalty), 1)
    return {
        "personnel": personnel, "readiness_score": readiness,
        "readiness_level": "GOOD" if readiness >= 75 else "STRAINED" if readiness >= 50 else "AT_RISK",
        "inventory": inv, "routes": routes, "assets": assets, "open_incidents": sos,
    }


def what_if(db: Session, scenario: str, resupply_in_days: float = 30.0, month: Optional[int] = None) -> dict:
    personnel = _personnel(db)
    inv = [{"item": i.item, "quantity": i.quantity, "daily_consumption": i.daily_consumption, "critical_days": i.critical_days}
           for i in db.query(Inventory).all()]
    return simulation_engine.run(scenario, inv, personnel=personnel, resupply_in_days=resupply_in_days, month=month)
