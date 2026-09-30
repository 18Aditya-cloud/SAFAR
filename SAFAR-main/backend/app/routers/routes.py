from fastapi import APIRouter, HTTPException
from pathlib import Path
import json


router = APIRouter(
    prefix="/routes",
    tags=["Transport & Routes"]
)


# ------------------------------------------------------------
# GeoJSON file location
# ------------------------------------------------------------

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

ROUTES_FILE = DATA_DIR / "routes.geojson"
STATIONS_FILE = DATA_DIR / "stations.geojson"
FACILITIES_FILE = DATA_DIR / "facilities.geojson"


# ------------------------------------------------------------
# Helper
# ------------------------------------------------------------

def load_geojson(file_path: Path):
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"GeoJSON file not found: {file_path.name}"
        )

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid GeoJSON file: {file_path.name}"
        )


# ------------------------------------------------------------
# GET ALL ROUTES
# ------------------------------------------------------------

@router.get("/")
def get_routes():
    return load_geojson(ROUTES_FILE)


# ------------------------------------------------------------
# GET ALL STATIONS
# ------------------------------------------------------------

@router.get("/stations")
def get_stations():
    return load_geojson(STATIONS_FILE)


# ------------------------------------------------------------
# GET ALL FACILITIES
# ------------------------------------------------------------

@router.get("/facilities")
def get_facilities():
    return load_geojson(FACILITIES_FILE)


# ------------------------------------------------------------
# GET ROUTE SUMMARY
# ------------------------------------------------------------

@router.get("/summary")
def get_route_summary():

    routes = load_geojson(ROUTES_FILE)
    stations = load_geojson(STATIONS_FILE)
    facilities = load_geojson(FACILITIES_FILE)

    return {
        "route_count": len(
            routes.get("features", [])
        ),
        "station_count": len(
            stations.get("features", [])
        ),
        "facility_count": len(
            facilities.get("features", [])
        ),
        "offline_source": True,
    }