from typing import Optional

from pydantic import BaseModel


# ============================================================
# EXPEDITIONS
# ============================================================

class ExpeditionCreate(BaseModel):
    name: str
    station: str
    personnel_count: int = 0
    status: str = "ACTIVE"


# ============================================================
# INVENTORY
# ============================================================

class InventoryCreate(BaseModel):
    item: str
    category: str
    quantity: float
    unit: str = "units"
    daily_consumption: float = 0
    critical_days: float = 7
    location: str = "Maitri"


# ============================================================
# ASSETS
# ============================================================

class AssetCreate(BaseModel):
    name: str
    asset_type: str
    location: str = "Maitri"
    status: str = "AVAILABLE"
    risk_score: float = 0


# ============================================================
# SOS / EMERGENCY
# ============================================================

class SOSCreate(BaseModel):
    incident_type: str
    severity: str = "HIGH"
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None


# ============================================================
# SIMULATION
# ============================================================

class SimulationCreate(BaseModel):
    scenario: str
    duration_days: int = 7


# ============================================================
# CARGO
# ============================================================

class CargoCreate(BaseModel):
    cargo_code: str
    description: str
    category: str

    quantity: float = 1
    weight_kg: float = 0

    origin: str = "NCPOR Goa"
    destination: str

    transport_mode: str = "VOYAGE"
    priority: str = "NORMAL"

    required_by: Optional[str] = None

    status: str = "PLANNED"
    current_location: str = "NCPOR Goa"

    expedition_id: Optional[int] = None


class CargoResponse(CargoCreate):
    id: int

    class Config:
        from_attributes = True