from .database import Base, engine, SessionLocal

from .models import (
    Expedition,
    Inventory,
    Asset,
    Cargo,
)


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# DATABASE SESSION
# ============================================================

db = SessionLocal()


# ============================================================
# EXPEDITIONS
# ============================================================

if db.query(Expedition).count() == 0:

    db.add_all([
        Expedition(
            name="Winter Scientific Expedition",
            station="Maitri",
            personnel_count=42,
            status="ACTIVE",
        ),

        Expedition(
            name="Coastal Research Mission",
            station="Bharati",
            personnel_count=28,
            status="PLANNED",
        ),
    ])


# ============================================================
# INVENTORY
# ============================================================

if db.query(Inventory).count() == 0:

    db.add_all([
        Inventory(
            item="Food Supplies",
            category="FOOD",
            quantity=1800,
            unit="kg",
            daily_consumption=180,
            critical_days=7,
            location="Maitri",
        ),

        Inventory(
            item="Diesel Fuel",
            category="FUEL",
            quantity=4200,
            unit="L",
            daily_consumption=350,
            critical_days=5,
            location="Maitri",
        ),

        Inventory(
            item="Medical Kits",
            category="MEDICAL",
            quantity=46,
            unit="kits",
            daily_consumption=1,
            critical_days=10,
            location="Maitri",
        ),

        Inventory(
            item="Spare Parts",
            category="MAINTENANCE",
            quantity=32,
            unit="units",
            daily_consumption=0.5,
            critical_days=14,
            location="Bharati",
        ),
    ])


# ============================================================
# ASSETS
# ============================================================

if db.query(Asset).count() == 0:

    db.add_all([
        Asset(
            name="Tracked Vehicle V-01",
            asset_type="VEHICLE",
            location="Maitri",
            status="AVAILABLE",
            risk_score=18,
        ),

        Asset(
            name="Tracked Vehicle V-02",
            asset_type="VEHICLE",
            location="Maitri",
            status="AVAILABLE",
            risk_score=31,
        ),

        Asset(
            name="Generator G-01",
            asset_type="GENERATOR",
            location="Maitri",
            status="MAINTENANCE",
            risk_score=62,
        ),

        Asset(
            name="Medical Unit M-01",
            asset_type="MEDICAL",
            location="Bharati",
            status="AVAILABLE",
            risk_score=12,
        ),
    ])


# ============================================================
# CARGO
# ============================================================

if db.query(Cargo).count() == 0:

    db.add_all([
        Cargo(
            cargo_code="C-001",
            description="Diesel Fuel",
            category="FUEL",
            quantity=4200,
            weight_kg=3600,
            origin="NCPOR Goa",
            destination="Maitri",
            transport_mode="VOYAGE",
            priority="CRITICAL",
            required_by="2026-12-20",
            status="PLANNED",
            current_location="NCPOR Goa",
        ),

        Cargo(
            cargo_code="C-002",
            description="Food Supplies",
            category="FOOD",
            quantity=1800,
            weight_kg=1800,
            origin="NCPOR Goa",
            destination="Bharati",
            transport_mode="VOYAGE",
            priority="HIGH",
            required_by="2026-12-25",
            status="PACKED",
            current_location="NCPOR Goa",
        ),

        Cargo(
            cargo_code="C-003",
            description="Medical Equipment",
            category="MEDICAL",
            quantity=25,
            weight_kg=450,
            origin="NCPOR Goa",
            destination="Maitri",
            transport_mode="AIR",
            priority="CRITICAL",
            required_by="2026-12-15",
            status="IN_TRANSIT",
            current_location="Cape Town",
        ),

        Cargo(
            cargo_code="C-004",
            description="Spare Parts",
            category="MAINTENANCE",
            quantity=40,
            weight_kg=600,
            origin="NCPOR Goa",
            destination="Bharati",
            transport_mode="VOYAGE",
            priority="NORMAL",
            required_by="2027-01-10",
            status="PLANNED",
            current_location="NCPOR Goa",
        ),
    ])


# ============================================================
# SAVE CHANGES
# ============================================================

db.commit()

db.close()

print("SAFAR seed data created successfully.")