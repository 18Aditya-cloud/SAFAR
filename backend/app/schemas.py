from pydantic import BaseModel
from typing import Optional

class ExpeditionCreate(BaseModel):
    name: str
    station: str
    personnel_count: int = 0
    status: str = "ACTIVE"

class InventoryCreate(BaseModel):
    item: str
    category: str
    quantity: float
    unit: str = "units"
    daily_consumption: float = 0
    critical_days: float = 7
    location: str = "Maitri"

class AssetCreate(BaseModel):
    name: str
    asset_type: str
    location: str = "Maitri"
    status: str = "AVAILABLE"
    risk_score: float = 0

class SOSCreate(BaseModel):
    incident_type: str
    severity: str = "HIGH"
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None

class SimulationCreate(BaseModel):
    scenario: str
    duration_days: int = 7
