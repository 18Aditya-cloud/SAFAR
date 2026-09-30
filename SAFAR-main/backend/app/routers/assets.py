from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Asset
from ..schemas import AssetCreate

router = APIRouter()

@router.get("/assets")
def list_assets(db: Session = Depends(get_db)):
    return db.query(Asset).all()

@router.post("/assets")
def create_asset(payload: AssetCreate, db: Session = Depends(get_db)):
    item = Asset(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
