from pathlib import Path
import json
import math


# ------------------------------------------------------------
# DATA LOCATION
# ------------------------------------------------------------

DATA_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    / "data"
)

ROUTES_FILE = DATA_DIR / "routes.geojson"


# ------------------------------------------------------------
# LOAD ROUTE DATA
# ------------------------------------------------------------

def load_routes():

    if not ROUTES_FILE.exists():
        return {
            "type": "FeatureCollection",
            "features": []
        }

    with open(
        ROUTES_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ------------------------------------------------------------
# HAVERSINE DISTANCE
# ------------------------------------------------------------

def haversine_distance(
    lat1,
    lon1,
    lat2,
    lon2
):
    """
    Calculate approximate distance between
    two geographic coordinates in kilometres.
    """

    earth_radius = 6371.0

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        +
        math.cos(lat1)
        * math.cos(lat2)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return earth_radius * c


# ------------------------------------------------------------
# ROUTE DISTANCE
# ------------------------------------------------------------

def calculate_route_distance(coordinates):

    total_distance = 0.0

    for index in range(
        len(coordinates) - 1
    ):

        lon1, lat1 = coordinates[index]
        lon2, lat2 = coordinates[index + 1]

        total_distance += haversine_distance(
            lat1,
            lon1,
            lat2,
            lon2
        )

    return round(
        total_distance,
        2
    )


# ------------------------------------------------------------
# ANALYZE ROUTES
# ------------------------------------------------------------

def analyze_routes():

    data = load_routes()

    results = []

    for feature in data.get(
        "features",
        []
    ):

        geometry = feature.get(
            "geometry",
            {}
        )

        properties = feature.get(
            "properties",
            {}
        )

        coordinates = geometry.get(
            "coordinates",
            []
        )

        if geometry.get("type") == "LineString":

            distance = calculate_route_distance(
                coordinates
            )

        else:
            distance = 0

        results.append({
            "name": properties.get(
                "name",
                "Unnamed Route"
            ),
            "type": properties.get(
                "type",
                "UNKNOWN"
            ),
            "distance_km": distance,
            "properties": properties,
        })

    return results


# ------------------------------------------------------------
# FIND ROUTE OPTIONS
# ------------------------------------------------------------

def get_route_options():

    routes = analyze_routes()

    return sorted(
        routes,
        key=lambda route:
        route["distance_km"]
    )