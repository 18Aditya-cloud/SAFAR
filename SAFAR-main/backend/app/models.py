from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from datetime import datetime

from .database import Base


# ============================================================
# EXPEDITIONS
# ============================================================

class Expedition(Base):
    __tablename__ = "expeditions"

    id = Column(Integer, primary_key=True)

    name = Column(String(120), nullable=False)
    station = Column(String(120), nullable=False)

    status = Column(String(40), default="ACTIVE")

    personnel_count = Column(Integer, default=0)

    start_date = Column(String(30), nullable=True)
    end_date = Column(String(30), nullable=True)


# ============================================================
# INVENTORY
# ============================================================

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)

    item = Column(String(120), nullable=False)
    category = Column(String(60), nullable=False)

    quantity = Column(Float, default=0)
    unit = Column(String(20), default="units")

    daily_consumption = Column(Float, default=0)
    critical_days = Column(Float, default=7)

    location = Column(String(120), default="Maitri")


# ============================================================
# ASSETS
# ============================================================

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True)

    name = Column(String(120), nullable=False)
    asset_type = Column(String(60), nullable=False)

    location = Column(String(120), default="Maitri")

    status = Column(String(40), default="AVAILABLE")

    risk_score = Column(Float, default=0)


# ============================================================
# SOS / EMERGENCY EVENTS
# ============================================================

class SOSEvent(Base):
    __tablename__ = "sos_events"

    id = Column(Integer, primary_key=True)

    incident_type = Column(String(100), nullable=False)
    severity = Column(String(30), default="HIGH")

    location = Column(String(120), nullable=False)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    description = Column(Text, nullable=True)

    status = Column(String(40), default="QUEUED_LOCAL")

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# SIMULATIONS
# ============================================================

class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(Integer, primary_key=True)

    scenario = Column(String(120), nullable=False)

    impact_score = Column(Float, default=0)

    risk_before = Column(String(30), default="LOW")
    risk_after = Column(String(30), default="MEDIUM")

    recommendation = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )


# ============================================================
# CARGO
# ============================================================

class Cargo(Base):
    __tablename__ = "cargo"

    id = Column(Integer, primary_key=True)

    # Cargo identification
    cargo_code = Column(
        String(50),
        unique=True,
        nullable=False
    )

    description = Column(
        String(200),
        nullable=False
    )

    category = Column(
        String(60),
        nullable=False
    )

    # Quantity and weight
    quantity = Column(
        Float,
        default=1
    )

    weight_kg = Column(
        Float,
        default=0
    )

    # Logistics
    origin = Column(
        String(120),
        default="NCPOR Goa"
    )

    destination = Column(
        String(120),
        nullable=False
    )

    # Transportation
    transport_mode = Column(
        String(40),
        default="VOYAGE"
    )

    priority = Column(
        String(30),
        default="NORMAL"
    )

    # Deadline
    required_by = Column(
        String(30),
        nullable=True
    )

    # Current logistics state
    status = Column(
        String(40),
        default="PLANNED"
    )

    current_location = Column(
        String(120),
        default="NCPOR Goa"
    )

    # Optional expedition association
    expedition_id = Column(
        Integer,
        nullable=True
    )