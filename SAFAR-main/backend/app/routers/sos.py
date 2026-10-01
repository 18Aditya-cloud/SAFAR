from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import SOSEvent
from ..schemas import SOSCreate

router = APIRouter()

@router.get("/sos")
def list_sos(db: Session = Depends(get_db)):
    return db.query(SOSEvent).order_by(SOSEvent.created_at.desc()).all()

@router.post("/sos")
def create_sos(payload: SOSCreate, db: Session = Depends(get_db)):
    event = SOSEvent(**payload.model_dump(), status="QUEUED_LOCAL")
    db.add(event)
    db.commit()
    db.refresh(event)
    return {
        "event": event,
        "message": "SOS stored locally. Remote transmission requires an available communication channel."
    }
