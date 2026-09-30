"""Offline queue sync + model manifest (versioning/integrity for edge deployment)."""
import hashlib
import json
from datetime import datetime

from sqlalchemy.orm import Session

from ml.config import MODELS_DIR
from ..models import SOSEvent
from . import risk_engine

SEV_RANK = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}


def pending_queue(db: Session) -> list:
    rows = db.query(SOSEvent).filter(SOSEvent.status == "QUEUED_LOCAL").all()
    out = []
    for r in rows:
        t = risk_engine.triage_sos(r.description or r.incident_type)
        out.append({"id": r.id, "incident_type": r.incident_type, "severity_ml": t["severity"], "severity_reported": r.severity,
                    "created_at": r.created_at.isoformat() if r.created_at else None})
    return sorted(out, key=lambda x: (min(SEV_RANK.get(x["severity_ml"], 3), SEV_RANK.get(x["severity_reported"], 3)), x["id"]))


def flush_sos(db: Session, channel_available: bool) -> dict:
    """Transmit queued SOS events most-severe-first when a channel exists. Transmission itself is simulated here."""
    queue = pending_queue(db)
    if not channel_available:
        return {"channel_available": False, "sent": 0, "pending": len(queue), "queue": queue,
                "message": "No communication channel: events remain safely queued locally."}
    ids = [q["id"] for q in queue]
    for r in db.query(SOSEvent).filter(SOSEvent.id.in_(ids)).all():
        r.status = "TRANSMITTED"
    db.commit()
    return {"channel_available": True, "sent": len(ids), "pending": 0, "order_sent": ids,
            "sent_at": datetime.utcnow().isoformat()}


def model_manifest() -> dict:
    files = []
    for p in sorted(MODELS_DIR.glob("*.joblib")):
        files.append({"file": p.name, "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()[:16]})
    metrics = json.loads((MODELS_DIR / "metrics.json").read_text()) if (MODELS_DIR / "metrics.json").exists() else {}
    return {"models": files, "trained_at": metrics.get("meta", {}).get("trained_at"), "data": metrics.get("meta", {}).get("data"),
            "update_policy": "Retrain when connectivity is available, verify checksum, then hot-swap joblib files."}
