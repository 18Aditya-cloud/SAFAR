from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import dashboard, expeditions, inventory, assets, sos, simulation

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SAFAR API",
    description="Offline-first Antarctic expedition decision-support API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api")
app.include_router(expeditions.router, prefix="/api")
app.include_router(inventory.router, prefix="/api")
app.include_router(assets.router, prefix="/api")
app.include_router(sos.router, prefix="/api")
app.include_router(simulation.router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "online-local", "service": "SAFAR"}
