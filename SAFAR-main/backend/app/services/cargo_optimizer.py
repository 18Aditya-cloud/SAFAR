"""Cargo loading optimiser (0/1 multi-constraint knapsack via scipy MILP)."""
from typing import Optional

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from ml.config import PRIORITY_WEIGHT, VESSEL


def optimise_cargo(items: list, capacity_kg: Optional[float] = None, capacity_m3: Optional[float] = None,
                   eta_days: float = 0.0, force_critical: bool = True) -> dict:
    """items: dicts with cargo_code, weight_kg, volume_m3 (optional), priority, deadline_days (optional), category.
    eta_days: pessimistic (P90) transit time; items whose deadline is earlier cannot make this sailing."""
    cap_kg = capacity_kg or VESSEL["capacity_kg"]
    cap_m3 = capacity_m3 or VESSEL["capacity_m3"]
    eligible, deferred = [], []
    for it in items:
        dl = it.get("deadline_days")
        if dl is not None and dl < eta_days:
            deferred.append({**it, "reason": f"Deadline in {dl} d is earlier than expected arrival (~{eta_days:.0f} d): needs faster mode"})
        else:
            eligible.append(it)
    if not eligible:
        return {"selected": [], "deferred": deferred, "utilisation": {}, "alerts": ["No eligible items"]}
    w = np.array([float(i["weight_kg"]) for i in eligible])
    v = np.array([float(i.get("volume_m3") or i["weight_kg"] / 1000 * 3.5) for i in eligible])
    val = np.array([PRIORITY_WEIGHT.get(str(i.get("priority", "NORMAL")).upper(), 20.0) for i in eligible])
    # value per item is the priority weight; small weight bonus makes the solver prefer fuller loads on ties
    obj = -(val + 0.001 * w)
    lb = np.zeros(len(eligible))
    crit = np.array([str(i.get("priority")).upper() == "CRITICAL" for i in eligible])
    alerts = []
    if force_critical and crit.any():
        if w[crit].sum() <= cap_kg and v[crit].sum() <= cap_m3:
            lb[crit] = 1
        else:
            alerts.append("Critical cargo alone exceeds vessel capacity: add a second sailing or air-lift")
    res = milp(c=obj, constraints=[LinearConstraint(np.vstack([w, v]), -np.inf, [cap_kg, cap_m3])],
               integrality=np.ones(len(eligible)), bounds=Bounds(lb, np.ones(len(eligible))))
    x = np.round(res.x).astype(bool) if res.success else np.zeros(len(eligible), bool)
    selected = [eligible[i] for i in range(len(eligible)) if x[i]]
    for i in range(len(eligible)):
        if not x[i]:
            deferred.append({**eligible[i], "reason": "Capacity reached: lower priority than loaded items"})
    for d in deferred:
        if str(d.get("priority")).upper() == "CRITICAL":
            alerts.append(f"Critical item {d.get('cargo_code')} not loaded: {d['reason']}")
    return {
        "selected": selected, "deferred": deferred,
        "utilisation": {"weight_kg": round(float(w[x].sum()), 1), "capacity_kg": cap_kg,
                        "weight_pct": round(100 * float(w[x].sum()) / cap_kg, 1),
                        "volume_m3": round(float(v[x].sum()), 1), "capacity_m3": cap_m3,
                        "volume_pct": round(100 * float(v[x].sum()) / cap_m3, 1)},
        "loaded_by_priority": {p: int(sum(1 for s in selected if str(s.get("priority")).upper() == p)) for p in PRIORITY_WEIGHT},
        "alerts": sorted(set(alerts)), "solver": "scipy-milp (HiGHS)", "status": "optimal" if res.success else "failed",
    }
