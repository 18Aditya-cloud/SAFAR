from .database import Base, engine, SessionLocal
from .models import Expedition, Inventory, Asset

Base.metadata.create_all(bind=engine)
db = SessionLocal()

if db.query(Expedition).count() == 0:
    db.add_all([
        Expedition(name="Winter Scientific Expedition", station="Maitri", personnel_count=42, status="ACTIVE"),
        Expedition(name="Coastal Research Mission", station="Bharati", personnel_count=28, status="PLANNED"),
    ])

if db.query(Inventory).count() == 0:
    db.add_all([
        Inventory(item="Food Supplies", category="FOOD", quantity=1800, unit="kg", daily_consumption=180, critical_days=7, location="Maitri"),
        Inventory(item="Diesel Fuel", category="FUEL", quantity=4200, unit="L", daily_consumption=350, critical_days=5, location="Maitri"),
        Inventory(item="Medical Kits", category="MEDICAL", quantity=46, unit="kits", daily_consumption=1, critical_days=10, location="Maitri"),
        Inventory(item="Spare Parts", category="MAINTENANCE", quantity=32, unit="units", daily_consumption=0.5, critical_days=14, location="Bharati"),
    ])

if db.query(Asset).count() == 0:
    db.add_all([
        Asset(name="Tracked Vehicle V-01", asset_type="VEHICLE", location="Maitri", status="AVAILABLE", risk_score=18),
        Asset(name="Tracked Vehicle V-02", asset_type="VEHICLE", location="Maitri", status="AVAILABLE", risk_score=31),
        Asset(name="Generator G-01", asset_type="GENERATOR", location="Maitri", status="MAINTENANCE", risk_score=62),
        Asset(name="Medical Unit M-01", asset_type="MEDICAL", location="Bharati", status="AVAILABLE", risk_score=12),
    ])

db.commit()
db.close()
print("SAFAR seed data created.")
