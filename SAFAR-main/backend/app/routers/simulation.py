from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Expedition, Inventory, Simulation
from ..schemas import SimulationCreate
from ..services import simulation_engine

router = APIRouter()


@router.post("/simulate")
def simulate(payload: SimulationCreate, db: Session = Depends(get_db)):
    """Monte Carlo what-if. Keeps the original response fields so the existing frontend works."""
    personnel = sum(e.personnel_count or 0 for e in db.query(Expedition).all()) or 60
    inv = [{"item": i.item, "quantity": i.quantity, "daily_consumption": i.daily_consumption, "critical_days": i.critical_days}
           for i in db.query(Inventory).all()]
    res = simulation_engine.run(payload.scenario, inv, personnel=personnel)
    row = Simulation(scenario=payload.scenario, impact_score=res["impact_score"], risk_before=res["risk_before"],
                     risk_after=res["risk_after"], recommendation=res["recommendation"])
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "scenario": row.scenario, "impact_score": row.impact_score, "risk_before": row.risk_before,
            "risk_after": row.risk_after, "recommendation": row.recommendation, "created_at": row.created_at,
            "details": res}


@router.get("/simulations")
def simulations(db: Session = Depends(get_db)):
    return db.query(Simulation).order_by(Simulation.created_at.desc()).all()
