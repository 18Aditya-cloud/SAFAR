from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Simulation
from ..schemas import SimulationCreate

router = APIRouter()

@router.post("/simulate")
def simulate(payload: SimulationCreate, db: Session = Depends(get_db)):
    # MVP deterministic scenario engine. Replace/extend with real simulation logic.
    impact_map = {
        "Cargo delay": 32,
        "Vehicle failure": 45,
        "Fuel shortage": 55,
        "Food shortage": 68,
        "Severe weather": 60,
        "Medical emergency": 75,
    }
    impact = impact_map.get(payload.scenario, 25)
    after = "HIGH" if impact >= 50 else "MEDIUM"
    recommendation = (
        "Prioritize critical cargo, protect emergency reserves, "
        "recalculate available routes and allocate backup resources."
    )
    row = Simulation(
        scenario=payload.scenario,
        impact_score=impact,
        risk_before="LOW",
        risk_after=after,
        recommendation=recommendation,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

@router.get("/simulations")
def simulations(db: Session = Depends(get_db)):
    return db.query(Simulation).order_by(Simulation.created_at.desc()).all()
