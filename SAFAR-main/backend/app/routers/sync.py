from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import sync_engine

router = APIRouter(prefix="/sync", tags=["Offline Sync"])


@router.get("/status")
def status(db: Session = Depends(get_db)):
    q = sync_engine.pending_queue(db)
    return {"mode": "OFFLINE-FIRST", "pending_sos": len(q), "queue": q}


@router.post("/flush")
def flush(channel_available: bool = False, db: Session = Depends(get_db)):
    return sync_engine.flush_sos(db, channel_available)


@router.get("/models")
def models():
    return sync_engine.model_manifest()
