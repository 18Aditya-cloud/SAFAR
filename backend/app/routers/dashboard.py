from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Expedition, Inventory, Asset, SOSEvent

router = APIRouter()

@router.get("/dashboard")
def dashboard_summary(db: Session = Depends(get_db)):
    inventory = db.query(Inventory).all()
    inventory_risk = []
    for item in inventory:
        days_left = (item.quantity / item.daily_consumption) if item.daily_consumption > 0 else 999
        inventory_risk.append({
            "item": item.item,
            "days_left": round(days_left, 1),
            "status": "CRITICAL" if days_left <= item.critical_days else "SAFE"
        })

    return {
        "expeditions": db.query(Expedition).count(),
        "inventory_items": len(inventory),
        "assets": db.query(Asset).count(),
        "open_sos": db.query(SOSEvent).filter(SOSEvent.status != "RESOLVED").count(),
        "inventory_risk": inventory_risk,
        "connectivity": "OFFLINE-FIRST",
    }
