from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services import digital_twin as twin
from ..services._ml_store import metrics, models_ready

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/model-metrics")
def model_metrics():
    """Evaluation metrics from the last training run (synthetic data)."""
    return {"models_ready": models_ready(), "metrics": metrics()}


@router.get("/summary")
def summary(month: Optional[int] = None, db: Session = Depends(get_db)):
    t = twin.build_twin(db, month)
    worst_route = max(t["routes"], key=lambda r: r["risk_score"])
    critical = [i for i in t["inventory"] if i["status"] in ("CRITICAL", "WATCH")]
    return {
        "readiness_score": t["readiness_score"], "readiness_level": t["readiness_level"],
        "highest_risk_route": {k: worst_route[k] for k in ("leg_id", "name", "risk_score", "risk_level", "top_factors")},
        "stock_alerts": [{"item": i["item"], "status": i["status"], "days_left": i["days_left"], "stockout_date": i["stockout_date"]}
                         for i in critical],
        "assets_at_risk": [a["name"] for a in t["assets"] if (a["predicted_failure_30d"] or 0) >= 0.5],
        "open_incidents": len(t["open_incidents"]),
    }
