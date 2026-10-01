"""Route analysis + risk-weighted multi-modal route optimisation."""
import heapq
import json
import math
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ROUTES_FILE = DATA_DIR / "routes.geojson"
STATIONS_FILE = DATA_DIR / "stations.geojson"
FACILITIES_FILE = DATA_DIR / "facilities.geojson"
SNAP_KM = 150.0  # route endpoints within this distance of a facility/station are snapped to it


def _load(path: Path):
    if not path.exists():
        return {"type": "FeatureCollection", "features": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_routes():
    return _load(ROUTES_FILE)


def haversine_distance(lat1, lon1, lat2, lon2):
    """Great-circle distance in km (fixed: original converted lat to radians before taking deltas)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def calculate_route_distance(coordinates):
    total = 0.0
    for (lon1, lat1), (lon2, lat2) in zip(coordinates, coordinates[1:]):
        total += haversine_distance(lat1, lon1, lat2, lon2)
    return round(total, 2)


def analyze_routes():
    results = []
    for f in load_routes().get("features", []):
        g, p = f.get("geometry", {}), f.get("properties", {})
        dist = calculate_route_distance(g["coordinates"]) if g.get("type") == "LineString" else 0
        results.append({"id": p.get("id"), "name": p.get("name", "Unnamed Route"), "type": p.get("type", "UNKNOWN"),
                        "distance_km": dist, "properties": p})
    return results


def get_route_options():
    return sorted(analyze_routes(), key=lambda r: r["distance_km"])


# ---------------------------------------------------------------- graph
def _nodes():
    nodes = {}
    for path in (FACILITIES_FILE, STATIONS_FILE):
        for f in _load(path).get("features", []):
            if f["geometry"]["type"] == "Point":
                lon, lat = f["geometry"]["coordinates"][:2]
                nodes[f["properties"]["name"]] = (lat, lon)
    return nodes


def _snap(nodes, lon, lat):
    best = min(nodes, key=lambda n: haversine_distance(lat, lon, *nodes[n]))
    return best if haversine_distance(lat, lon, *nodes[best]) <= SNAP_KM else None


def build_graph():
    nodes = _nodes()
    edges = []
    for f in load_routes().get("features", []):
        g, p = f["geometry"], f["properties"]
        if g["type"] != "LineString":
            continue
        a, b = _snap(nodes, *g["coordinates"][0]), _snap(nodes, *g["coordinates"][-1])
        if a and b and a != b:
            edges.append({"id": p["id"], "from": a, "to": b, "mode": p.get("mode"), "name": p.get("name"),
                          "distance_km": calculate_route_distance(g["coordinates"]), "days": float(p.get("estimated_days", 1))})
    return nodes, edges


def _paths(edges, origin, dest):
    adj = {}
    for e in edges:  # corridors are bidirectional
        adj.setdefault(e["from"], []).append((e["to"], e))
        adj.setdefault(e["to"], []).append((e["from"], e))
    out, stack = [], [(origin, [], {origin})]
    while stack:
        node, path, seen = stack.pop()
        if node == dest:
            out.append(path)
            continue
        for nxt, e in adj.get(node, []):
            if nxt not in seen:
                stack.append((nxt, path + [e], seen | {nxt}))
    return out


def _resolve(name: str, nodes: dict, connected: set) -> str:
    """Accept 'Maitri' for 'Maitri Logistics Facility' etc.; prefer nodes that are on the route graph."""
    if name in connected:
        return name
    hits = [n for n in connected if name.lower() in n.lower() or n.lower() in name.lower()]
    if hits:
        return sorted(hits)[0]
    raise KeyError(f"Unknown node '{name}'. Known: {sorted(connected)}")


def find_routes(origin: str, destination: str, risk_by_route: Optional[dict] = None, eta_by_route: Optional[dict] = None,
                risk_aversion: float = 1.0) -> list:
    """Enumerate paths, rank by cost = days * (1 + risk_aversion * risk). Returns best-first alternatives."""
    nodes, edges = build_graph()
    connected = {e["from"] for e in edges} | {e["to"] for e in edges}
    origin, destination = _resolve(origin, nodes, connected), _resolve(destination, nodes, connected)
    risk_by_route, eta_by_route = risk_by_route or {}, eta_by_route or {}
    results = []
    for path in _paths(edges, origin, destination):
        days = sum(eta_by_route.get(e["id"], e["days"]) for e in path)
        surv = 1.0
        for e in path:
            surv *= 1 - risk_by_route.get(e["id"], 0.3)
        risk = 1 - surv
        cost = sum(eta_by_route.get(e["id"], e["days"]) * (1 + risk_aversion * risk_by_route.get(e["id"], 0.3)) for e in path)
        results.append({"path": [origin] + [e["to"] if e["from"] == (origin if i == 0 else path[i - 1]["to"]) else e["from"] for i, e in enumerate(path)],
                        "legs": [e["id"] for e in path], "modes": [e["mode"] for e in path],
                        "total_days": round(days, 1), "distance_km": round(sum(e["distance_km"] for e in path), 1),
                        "route_risk": round(risk, 3), "cost": round(cost, 2)})
    results.sort(key=lambda r: r["cost"])
    for i, r in enumerate(results):
        r["rank"] = i + 1
        r["label"] = "Recommended" if i == 0 else "Alternative"
    fastest = min(results, key=lambda r: r["total_days"], default=None)
    safest = min(results, key=lambda r: r["route_risk"], default=None)
    for r in results:
        if r is fastest and r["rank"] != 1:
            r["label"] = "Fastest"
        if r is safest and r["rank"] != 1:
            r["label"] = "Safest"
    return results
