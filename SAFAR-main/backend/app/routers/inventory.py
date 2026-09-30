from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Inventory
from ..schemas import InventoryCreate

router = APIRouter()

@router.get("/inventory")
def list_inventory(db: Session = Depends(get_db)):
    rows = db.query(Inventory).all()
    result = []
    for row in rows:
        days_left = (row.quantity / row.daily_consumption) if row.daily_consumption > 0 else 999
        result.append({
            "id": row.id,
            "item": row.item,
            "category": row.category,
            "quantity": row.quantity,
            "unit": row.unit,
            "location": row.location,
            "daily_consumption": row.daily_consumption,
            "days_left": round(days_left, 1),
            "status": "CRITICAL" if days_left <= row.critical_days else "SAFE"
        })
    return result

@router.post("/inventory")
def create_inventory(payload: InventoryCreate, db: Session = Depends(get_db)):
    item = Inventory(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
