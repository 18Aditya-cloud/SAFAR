from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import digital_twin as twin
from ..services.simulation_engine import SCENARIOS

router = APIRouter(prefix="/digital-twin", tags=["Digital Twin"])


class WhatIf(BaseModel):
    scenario: str
    resupply_in_days: float = 30.0
    month: Optional[int] = None


@router.get("")
def state(month: Optional[int] = None, db: Session = Depends(get_db)):
    return twin.build_twin(db, month)


@router.get("/scenarios")
def scenarios():
    return sorted(SCENARIOS)


@router.post("/what-if")
def what_if(req: WhatIf, db: Session = Depends(get_db)):
    return twin.what_if(db, req.scenario, req.resupply_in_days, req.month)
