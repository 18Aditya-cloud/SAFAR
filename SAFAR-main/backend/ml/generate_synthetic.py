"""Generate SAFAR synthetic datasets (seeded, reproducible).

Run from backend/:  python -m ml.generate_synthetic
All data is SYNTHETIC. Patterns are modelled on known Antarctic logistics
seasonality (austral summer Nov-Mar = operating window) but are not real records.
"""
import numpy as np
import pandas as pd

from .config import DATA_DIR, LEGS, REGIONS, SEED, INVENTORY_ITEMS, ASSET_TYPES

rng = np.random.default_rng(SEED)
DATES = pd.date_range("2021-01-01", "2025-12-31", freq="D")


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def summer_index(dates):
    """+1 at mid-January (austral summer), -1 at mid-July."""
    doy = dates.dayofyear.to_numpy()
    return np.cos(2 * np.pi * (doy - 15) / 365.0)


def ar1(n, phi, sigma):
    x = np.zeros(n)
    for t in range(1, n):
        x[t] = phi * x[t - 1] + rng.normal(0, sigma)
    return x


# ---------------------------------------------------------------- weather
def make_weather():
    prm = {  # temp_base, temp_amp, wind_base, wind_amp, ice_base, ice_amp
        "INDIAN_OCEAN": (26, 2.5, 13, 3, 0.0, 0.0),
        "SOUTHERN_OCEAN": (1, 5, 24, 9, 0.38, 0.34),
        "ANTARCTIC": (-12, 11, 22, 10, 0.72, 0.22),
    }
    s = summer_index(DATES)
    frames = []
    for region in REGIONS:
        tb, ta, wb, wa, ib, ia = prm[region]
        n = len(DATES)
        wind = np.clip(wb + wa * (1 - s) / 2 + 6 * ar1(n, 0.85, 0.6), 2, 75)
        wave = np.clip(0.05 * wind + 0.9 * ar1(n, 0.8, 0.4) + (1.2 if region != "INDIAN_OCEAN" else 0.6), 0.2, 12)
        if region == "ANTARCTIC":
            wave = wave * 0.0
        ice = np.clip(ib - ia * s + 0.08 * ar1(n, 0.9, 0.5), 0, 1) if ib > 0 else np.zeros(n)
        temp = tb + ta * s + 2.5 * ar1(n, 0.85, 0.6)
        blizzard = ((wind > 38) & (rng.random(n) < 0.6) & (region != "INDIAN_OCEAN")).astype(int)
        vis = np.clip(20 - 0.28 * wind - 10 * blizzard + rng.normal(0, 1.5, n), 0.1, 25)
        frames.append(pd.DataFrame({
            "date": DATES, "region": region, "temp_c": temp.round(1), "wind_kts": wind.round(1),
            "wave_m": wave.round(2), "sea_ice_conc": ice.round(3), "visibility_km": vis.round(1),
            "blizzard": blizzard,
        }))
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------- voyages
def make_voyages(weather, n=3200):
    wx = weather.set_index(["date", "region"])
    legs = list(LEGS)
    probs = np.array([0.22, 0.2, 0.2, 0.18, 0.2])
    rows = []
    for i in range(n):
        leg = rng.choice(legs, p=probs)
        info = LEGS[leg]
        if leg in ("R003", "R004", "R005") and rng.random() < 0.85:  # summer window
            year = rng.integers(2021, 2026)
            start = pd.Timestamp(year=int(year), month=11, day=1)
            date = start + pd.Timedelta(days=int(rng.integers(0, 150)))
            if date > DATES[-1]:
                date = date - pd.DateOffset(years=1)
        else:
            date = DATES[int(rng.integers(0, len(DATES)))]
        w = wx.loc[(date, info["region"])]
        cargo_t = float(np.clip(rng.normal(40, 15), 2, 90))
        vessel_age = float(np.clip(rng.normal(14, 6), 1, 35))
        crew_exp = float(np.clip(rng.normal(8, 4), 0.5, 25))
        planned = max(1, int(round(info["planned_days"] * rng.uniform(0.92, 1.1))))
        z = (-1.6 + info["base_risk"] + 0.05 * (w.wind_kts - 20) + 0.28 * (w.wave_m - 2.5)
             + 2.0 * w.sea_ice_conc - 0.05 * (w.visibility_km - 12) + 0.7 * w.blizzard
             + 0.02 * (cargo_t - 40) + 0.03 * (vessel_age - 14) - 0.06 * (crew_exp - 8)
             + rng.normal(0, 0.35))
        p = float(sigmoid(z))
        occurs = rng.random() < min(1.0, 0.12 + 1.4 * p)
        delay = planned * 0.5 * p * rng.lognormal(0, 0.5) * occurs
        incident = int(rng.random() < sigmoid(z - 2.8))
        rows.append({
            "voyage_id": f"V{i:05d}", "leg_id": leg, "mode": info["mode"], "depart_date": date.date(),
            "planned_days": planned, "cargo_t": round(cargo_t, 1), "vessel_age_yr": round(vessel_age, 1),
            "crew_experience_yr": round(crew_exp, 1), "temp_c": w.temp_c, "wind_kts": w.wind_kts,
            "wave_m": w.wave_m, "sea_ice_conc": w.sea_ice_conc, "visibility_km": w.visibility_km,
            "blizzard": int(w.blizzard), "delay_days": round(float(delay), 2),
            "actual_days": round(planned + float(delay), 2),
            "delayed": int(delay >= 0.1 * planned), "incident": incident,
        })
    return pd.DataFrame(rows).sort_values("depart_date").reset_index(drop=True)


# ---------------------------------------------------------------- inventory
ITEM_PARAMS = {  # base, per_person, cold_coeff, unit
    "Food Supplies": (0.0, 1.8, 0.008, "kg"),
    "Diesel Fuel": (110.0, 2.4, 0.04, "L"),      # cold term is additive per person
    "Medical Kits": (0.05, 0.010, 0.0, "kits"),
    "Spare Parts": (0.05, 0.004, 0.02, "units"),
}


def make_inventory(weather):
    ant = weather[weather.region == "ANTARCTIC"].set_index("date")
    s = summer_index(DATES)
    personnel = np.clip(np.round(30 + 60 * (s + 1) / 2 + rng.normal(0, 3, len(DATES))), 20, 100)
    temp = ant.loc[DATES, "temp_c"].to_numpy()
    cold = np.maximum(0, -temp)
    rows = []
    for item in INVENTORY_ITEMS:
        base, per, cc, unit = ITEM_PARAMS[item]
        if item == "Diesel Fuel":
            raw = base + per * personnel + cc * cold * personnel / 10
        else:
            raw = (base + per * personnel) * (1 + cc * cold)
        cons = raw * rng.normal(1, 0.06, len(DATES))
        anomaly = rng.random(len(DATES)) < 0.015
        cons = np.where(anomaly, cons * rng.uniform(1.6, 2.5, len(DATES)), cons)
        rows.append(pd.DataFrame({
            "date": DATES, "item": item, "unit": unit, "personnel": personnel.astype(int),
            "temp_c": temp, "consumption": np.round(np.maximum(cons, 0), 2), "is_anomaly": anomaly.astype(int),
        }))
    return pd.concat(rows, ignore_index=True)


# ---------------------------------------------------------------- assets
def make_assets(n_assets=40, months=24):
    rows = []
    for a in range(n_assets):
        atype = ASSET_TYPES[a % len(ASSET_TYPES)]
        age0 = rng.uniform(0.5, 15)
        since_maint = rng.uniform(5, 120)
        for m in range(months):
            age = age0 + m / 12
            since_maint += 30
            if since_maint > rng.uniform(150, 240):
                since_maint = rng.uniform(0, 20)
            hours = float(np.clip(rng.normal(170, 60), 10, 420))
            temp = float(rng.normal(-14, 8))
            vib = float(np.clip(rng.normal(2.5 + 0.12 * age + 0.004 * since_maint, 0.6), 0.3, 12))
            oil_dev = float(np.clip(rng.normal(0.04 * age + 0.002 * since_maint, 0.15), -0.5, 3))
            load = float(np.clip(rng.normal(0.62, 0.18), 0.1, 1.0))
            z = (-4.0 + 0.12 * age + 0.012 * since_maint + 0.004 * (hours - 170) + 0.35 * (vib - 3)
                 + 1.1 * oil_dev + 1.0 * (load - 0.6) - 0.03 * (temp + 14) + rng.normal(0, 0.4))
            rows.append({
                "asset_id": f"A{a:03d}", "asset_type": atype, "month_index": m, "age_yr": round(age, 2),
                "operating_hours_30d": round(hours, 1), "avg_temp_c": round(temp, 1),
                "vibration_mm_s": round(vib, 2), "oil_pressure_dev": round(oil_dev, 3),
                "days_since_maintenance": int(since_maint), "load_factor": round(load, 2),
                "fault_next_30d": int(rng.random() < sigmoid(z)),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- SOS text
SOS_TEMPLATES = {
    "MEDICAL_EMERGENCY": [
        ("team member unconscious after fall, not breathing normally", "CRITICAL"),
        ("severe chest pain reported by field scientist", "CRITICAL"),
        ("suspected fracture in leg, patient stable", "HIGH"),
        ("frostbite on fingers of two crew, needs treatment", "HIGH"),
        ("mild hypothermia symptoms, being warmed in shelter", "MEDIUM"),
        ("minor cut on hand, first aid applied", "LOW"),
    ],
    "FIRE": [
        ("fire spreading in accommodation module, evacuation started", "CRITICAL"),
        ("smoke in generator hall, source not found", "HIGH"),
        ("small electrical fire in lab, extinguished", "MEDIUM"),
        ("burning smell from heater, switched off", "LOW"),
    ],
    "VEHICLE_FAILURE": [
        ("tracked vehicle immobilised far from station, night approaching", "HIGH"),
        ("vehicle engine overheating during traverse", "MEDIUM"),
        ("sledge tow bracket broken, cargo stable", "MEDIUM"),
        ("vehicle battery weak but can restart", "LOW"),
    ],
    "CREVASSE_ACCIDENT": [
        ("vehicle partially fallen into crevasse, crew trapped inside", "CRITICAL"),
        ("person slipped into crevasse, roped and conscious", "CRITICAL"),
        ("new crevasse spotted on route, marked and avoided", "LOW"),
    ],
    "POWER_FAILURE": [
        ("total power loss at station during blizzard", "CRITICAL"),
        ("main generator tripped, backup running", "HIGH"),
        ("intermittent voltage drops in lab wing", "MEDIUM"),
    ],
    "WEATHER_ENTRAPMENT": [
        ("field team trapped by whiteout, supplies for two days only", "HIGH"),
        ("strong katabatic winds, movement suspended, team sheltered", "MEDIUM"),
        ("visibility poor, delaying return by hours", "LOW"),
    ],
    "FUEL_LEAK": [
        ("large diesel spill near storage tank, ignition risk", "CRITICAL"),
        ("slow fuel leak from drum, contained with absorbent", "MEDIUM"),
        ("small drip at pump connector, tightened", "LOW"),
    ],
    "COMMUNICATION_LOSS": [
        ("lost contact with field team for six hours", "HIGH"),
        ("satellite link down, radio working", "MEDIUM"),
        ("weak signal at outpost, retrying", "LOW"),
    ],
    "SUPPLY_SHORTAGE": [
        ("food stock below critical level, resupply delayed", "HIGH"),
        ("medical kits nearly exhausted after incident", "HIGH"),
        ("spare parts running low for next month", "LOW"),
    ],
}
FILLERS = ["", "urgent", "please advise", "at Maitri", "near Bharati", "on traverse", "reported by radio", "team leader says"]


def make_sos(n=900):
    rows = []
    sev = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    for i in range(n):
        itype = rng.choice(list(SOS_TEMPLATES))
        text, s = SOS_TEMPLATES[itype][int(rng.integers(0, len(SOS_TEMPLATES[itype])))]
        label = s
        if rng.random() < 0.04:  # label noise
            label = sev[int(np.clip(sev.index(s) + rng.choice([-1, 1]), 0, 3))]
        pre, post = rng.choice(FILLERS), rng.choice(FILLERS)
        rows.append({"report_id": f"S{i:04d}", "text": " ".join(x for x in [pre, text, post] if x).strip(),
                     "incident_type": itype, "severity": label})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- cargo
def make_cargo(n=60):
    cats = {  # weight range kg, volume factor m3/t, priority probs (CRIT, HIGH, NORMAL, LOW)
        "FOOD": ((800, 3500), 2.2, [0.5, 0.3, 0.2, 0]),
        "FUEL": ((2000, 6000), 1.3, [0.5, 0.4, 0.1, 0]),
        "MEDICAL": ((50, 400), 4.0, [0.8, 0.2, 0, 0]),
        "SPARE_PARTS": ((100, 1500), 3.0, [0.2, 0.5, 0.3, 0]),
        "SCIENTIFIC": ((200, 2500), 4.5, [0, 0.3, 0.5, 0.2]),
        "CONSTRUCTION": ((1000, 5000), 3.5, [0, 0.1, 0.5, 0.4]),
        "COMMS": ((50, 600), 4.0, [0.1, 0.4, 0.4, 0.1]),
        "PPE": ((100, 900), 5.0, [0.2, 0.5, 0.3, 0]),
        "GENERAL": ((100, 2000), 3.5, [0, 0.1, 0.5, 0.4]),
    }
    prios = ["CRITICAL", "HIGH", "NORMAL", "LOW"]
    rows = []
    for i in range(n):
        cat = list(cats)[i % len(cats)] if i < 27 else rng.choice(list(cats))
        (lo, hi), vf, pp = cats[cat]
        w = float(rng.uniform(lo, hi))
        pr = rng.choice(prios, p=pp)
        rows.append({
            "cargo_code": f"C-{i+1:03d}", "description": f"{cat.title().replace('_', ' ')} lot {i+1}",
            "category": cat, "weight_kg": round(w, 1), "volume_m3": round(w / 1000 * vf * rng.uniform(0.8, 1.2), 2),
            "priority": pr, "deadline_days": int(rng.integers(20, 75)) if pr != "LOW" else int(rng.integers(45, 120)),
            "destination": "Maitri" if rng.random() < 0.6 else "Bharati",
        })
    return pd.DataFrame(rows)


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    weather = make_weather()
    out = {
        "weather_conditions.csv": weather,
        "voyage_history.csv": make_voyages(weather),
        "inventory_consumption.csv": make_inventory(weather),
        "asset_telemetry.csv": make_assets(),
        "sos_reports.csv": make_sos(),
        "cargo_manifest.csv": make_cargo(),
    }
    for name, df in out.items():
        df.to_csv(DATA_DIR / name, index=False)
        print(f"{name:28s} {len(df):>7,} rows")


if __name__ == "__main__":
    main()
