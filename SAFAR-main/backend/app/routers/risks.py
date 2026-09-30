from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Asset, Inventory
from ..services import risk_engine
from ..services.inventory_engine import detect_anomaly, forecast_inventory

router = APIRouter(prefix="/risks", tags=["AI Risk & Forecasting"])


class ScoreRequest(BaseModel):
    leg_id: str
    month: Optional[int] = None
    wind_kts: Optional[float] = None
    wave_m: Optional[float] = None
    sea_ice_conc: Optional[float] = None
    visibility_km: Optional[float] = None
    temp_c: Optional[float] = None
    blizzard: Optional[float] = None
    cargo_t: Optional[float] = None
    vessel_age_yr: Optional[float] = None
    crew_experience_yr: Optional[float] = None


class AnomalyRequest(BaseModel):
    item: str
    observed: float
    personnel: int = 60
    month: int


class TriageRequest(BaseModel):
    text: str


@router.get("/routes")
def route_risks(month: Optional[int] = None):
    """ML risk score, ETA P50/P90 and top drivers for every corridor."""
    return risk_engine.score_all_routes(month)


@router.post("/score")
def score(req: ScoreRequest):
    d = req.model_dump()
    overrides = {k: d.pop(k) for k in ("wind_kts", "wave_m", "sea_ice_conc", "visibility_km", "temp_c", "blizzard")}
    try:
        return risk_engine.score_route(d["leg_id"], d["month"], overrides, d["cargo_t"], d["vessel_age_yr"], d["crew_experience_yr"])
    except KeyError as e:
        raise HTTPException(404, str(e))


@router.get("/assets")
def asset_risks(db: Session = Depends(get_db)):
    out = []
    for a in db.query(Asset).all():
        out.append({"id": a.id, "name": a.name, "asset_type": a.asset_type, "recorded_risk": a.risk_score,
                    **risk_engine.score_asset(a.asset_type)})
    return out


@router.get("/inventory")
def inventory_forecast(personnel: int = 60, db: Session = Depends(get_db)):
    return forecast_inventory(db.query(Inventory).all(), personnel=personnel)


@router.post("/inventory/anomaly")
def inventory_anomaly(req: AnomalyRequest):
    return detect_anomaly(req.item, req.observed, req.personnel, req.month)


@router.post("/triage")
def triage(req: TriageRequest):
    return risk_engine.triage_sos(req.text)
