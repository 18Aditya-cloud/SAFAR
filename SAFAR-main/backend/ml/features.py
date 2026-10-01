"""Feature definitions shared by training and inference."""
import numpy as np
from .config import LEG_CODE, MODE_CODE, LEGS

VOYAGE_FEATURES = [
    "leg_code", "mode_code", "planned_days", "temp_c", "wind_kts", "wave_m", "sea_ice_conc",
    "visibility_km", "blizzard", "cargo_t", "vessel_age_yr", "crew_experience_yr", "month_sin", "month_cos",
]
ASSET_FEATURES = [
    "type_code", "age_yr", "operating_hours_30d", "avg_temp_c", "vibration_mm_s", "oil_pressure_dev",
    "days_since_maintenance", "load_factor",
]
INVENTORY_FEATURES = ["personnel", "temp_c", "month_sin", "month_cos"]


def voyage_frame(df):
    d = df.copy()
    d["leg_code"] = d["leg_id"].map(LEG_CODE)
    d["mode_code"] = d["leg_id"].map(lambda k: MODE_CODE[LEGS[k]["mode"]])
    m = d["month"] if "month" in d else __import__("pandas").to_datetime(d["depart_date"]).dt.month
    d["month_sin"] = np.sin(2 * np.pi * m / 12)
    d["month_cos"] = np.cos(2 * np.pi * m / 12)
    return d[VOYAGE_FEATURES]
