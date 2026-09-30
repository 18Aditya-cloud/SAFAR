from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Expedition
from ..schemas import ExpeditionCreate

router = APIRouter()

@router.get("/expeditions")
def list_expeditions(db: Session = Depends(get_db)):
    return db.query(Expedition).all()

@router.post("/expeditions")
def create_expedition(payload: ExpeditionCreate, db: Session = Depends(get_db)):
    item = Expedition(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
