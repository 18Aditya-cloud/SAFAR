from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine

from .routers import (
    dashboard,
    expeditions,
    inventory,
    assets,
    sos,
    simulation,
    cargo,
    routes,
    risks,
    optimization,
    digital_twin,
    sync,
    reports,
)


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="SAFAR API",
    description="Offline-first Antarctic expedition decision-support API",
    version="0.1.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# API ROUTES
# ============================================================

app.include_router(dashboard.router, prefix="/api")
app.include_router(expeditions.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(assets.router, prefix="/api")
app.include_router(sos.router, prefix="/api")
app.include_router(simulation.router, prefix="/api")
app.include_router(cargo.router, prefix="/api")

# TRANSPORT & ROUTES
app.include_router(routes.router, prefix="/api")

# AI / ML
app.include_router(risks.router, prefix="/api")
app.include_router(optimization.router, prefix="/api")
app.include_router(digital_twin.router, prefix="/api")
app.include_router(sync.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    from .services._ml_store import models_ready
    return {
        "status": "online-local",
        "service": "SAFAR",
        "ml_models_ready": models_ready(),
    }