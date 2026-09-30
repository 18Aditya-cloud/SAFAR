from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Cargo
from ..schemas import CargoCreate, CargoResponse


# ============================================================
# CARGO ROUTER
# ============================================================

router = APIRouter(
    prefix="/cargo",
    tags=["Cargo"]
)


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# GET ALL CARGO
# ============================================================

@router.get(
    "/",
    response_model=list[CargoResponse]
)
def get_cargo(
    db: Session = Depends(get_db)
):
    cargo = (
        db.query(Cargo)
        .order_by(Cargo.id.desc())
        .all()
    )

    return cargo


# ============================================================
# GET ONE CARGO ITEM
# ============================================================

@router.get(
    "/{cargo_id}",
    response_model=CargoResponse
)
def get_cargo_item(
    cargo_id: int,
    db: Session = Depends(get_db)
):
    cargo = (
        db.query(Cargo)
        .filter(Cargo.id == cargo_id)
        .first()
    )

    if not cargo:
        raise HTTPException(
            status_code=404,
            detail="Cargo not found"
        )

    return cargo


# ============================================================
# CREATE CARGO
# ============================================================

@router.post(
    "/",
    response_model=CargoResponse
)
def create_cargo(
    cargo_data: CargoCreate,
    db: Session = Depends(get_db)
):
    # Check whether cargo code already exists
    existing = (
        db.query(Cargo)
        .filter(
            Cargo.cargo_code == cargo_data.cargo_code
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Cargo code already exists"
        )

    cargo = Cargo(
        **cargo_data.model_dump()
    )

    db.add(cargo)
    db.commit()
    db.refresh(cargo)

    return cargo


# ============================================================
# UPDATE CARGO
# ============================================================

@router.put(
    "/{cargo_id}",
    response_model=CargoResponse
)
def update_cargo(
    cargo_id: int,
    cargo_data: CargoCreate,
    db: Session = Depends(get_db)
):
    cargo = (
        db.query(Cargo)
        .filter(Cargo.id == cargo_id)
        .first()
    )

    if not cargo:
        raise HTTPException(
            status_code=404,
            detail="Cargo not found"
        )

    # Prevent duplicate cargo codes
    existing = (
        db.query(Cargo)
        .filter(
            Cargo.cargo_code == cargo_data.cargo_code,
            Cargo.id != cargo_id
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Cargo code already exists"
        )

    # Update fields
    for key, value in cargo_data.model_dump().items():
        setattr(cargo, key, value)

    db.commit()
    db.refresh(cargo)

    return cargo


# ============================================================
# DELETE CARGO
# ============================================================

@router.delete(
    "/{cargo_id}"
)
def delete_cargo(
    cargo_id: int,
    db: Session = Depends(get_db)
):
    cargo = (
        db.query(Cargo)
        .filter(Cargo.id == cargo_id)
        .first()
    )

    if not cargo:
        raise HTTPException(
            status_code=404,
            detail="Cargo not found"
        )

    db.delete(cargo)
    db.commit()

    return {
        "message": "Cargo deleted successfully",
        "cargo_id": cargo_id
    }