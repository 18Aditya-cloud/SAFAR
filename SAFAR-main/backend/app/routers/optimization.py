from datetime import date, datetime
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ml.config import DATA_DIR
from ..database import get_db
from ..models import Cargo
from ..services import risk_engine
from ..services.cargo_optimizer import optimise_cargo
from ..services.route_engine import find_routes

router = APIRouter(prefix="/optimization", tags=["Optimisation"])


class CargoItem(BaseModel):
    cargo_code: str
    weight_kg: float
    volume_m3: Optional[float] = None
    priority: str = "NORMAL"
    deadline_days: Optional[int] = None
    category: Optional[str] = None
    description: Optional[str] = None


class CargoOptRequest(BaseModel):
    source: str = "db"  # "db" | "sample" | "custom"
    items: Optional[List[CargoItem]] = None
    leg_id: str = "R003"
    month: Optional[int] = None
    capacity_kg: Optional[float] = None
    capacity_m3: Optional[float] = None


def _db_items(db: Session):
    items = []
    for c in db.query(Cargo).filter(Cargo.status.in_(["PLANNED", "PENDING", "LOADING"])).all():
        dl = None
        if c.required_by:
            try:
                dl = (datetime.fromisoformat(c.required_by[:10]).date() - date.today()).days
            except ValueError:
                pass
        items.append({"cargo_code": c.cargo_code, "description": c.description, "category": c.category,
                      "weight_kg": (c.weight_kg or 0) * 1.0, "priority": (c.priority or "NORMAL").upper(), "deadline_days": dl})
    return items


@router.post("/cargo")
def optimise(req: CargoOptRequest, db: Session = Depends(get_db)):
    if req.source == "custom" and req.items:
        items = [i.model_dump() for i in req.items]
    elif req.source == "sample" or (req.source == "db" and not db.query(Cargo).count()):
        items = pd.read_csv(DATA_DIR / "cargo_manifest.csv").to_dict("records")
    else:
        items = _db_items(db)
    try:
        risk = risk_engine.score_route(req.leg_id, req.month)
    except KeyError as e:
        raise HTTPException(404, str(e))
    result = optimise_cargo(items, req.capacity_kg, req.capacity_m3, eta_days=risk["eta_days_p90"])
    result["sailing_risk"] = {k: risk[k] for k in ("leg_id", "risk_score", "risk_level", "eta_days_p50", "eta_days_p90")}
    return result


@router.get("/routes")
def optimise_routes(origin: str = "NCPOR Goa", destination: str = "Maitri", risk_aversion: float = 1.0, month: Optional[int] = None):
    """Risk-weighted route alternatives (time vs safety), using ML P90 ETAs."""
    scored = risk_engine.score_all_routes(month)
    risk = {r["leg_id"]: r["risk_score"] / 100 for r in scored}
    eta = {r["leg_id"]: r["eta_days_p90"] for r in scored}
    try:
        return find_routes(origin, destination, risk, eta, risk_aversion)
    except KeyError as e:
        raise HTTPException(404, str(e))
