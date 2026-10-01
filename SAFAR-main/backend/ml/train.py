"""Train all SAFAR models on the synthetic datasets.

Run from backend/:  python -m ml.train
Outputs: ml/models/*.joblib and ml/models/metrics.json
"""
import json
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import (GradientBoostingClassifier, GradientBoostingRegressor,
                              RandomForestClassifier)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, brier_score_loss, f1_score, mean_absolute_error,
                             roc_auc_score)
from sklearn.pipeline import make_pipeline

from .config import ASSET_TYPES, DATA_DIR, INVENTORY_ITEMS, MODELS_DIR, SEED
from .features import ASSET_FEATURES, INVENTORY_FEATURES, VOYAGE_FEATURES, voyage_frame

metrics = {}


def time_split(df, col, frac=0.8):
    df = df.sort_values(col)
    k = int(len(df) * frac)
    return df.iloc[:k], df.iloc[k:]


def train_voyage():
    df = pd.read_csv(DATA_DIR / "voyage_history.csv")
    tr, te = time_split(df, "depart_date")
    Xtr, Xte = voyage_frame(tr), voyage_frame(te)
    clf = GradientBoostingClassifier(n_estimators=250, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=SEED)
    clf.fit(Xtr, tr["delayed"])
    p = clf.predict_proba(Xte)[:, 1]
    # delay-days quantile models (ratio of planned so it generalises across legs)
    ytr = tr["delay_days"] / tr["planned_days"]
    q = {}
    for name, alpha in (("p50", 0.5), ("p90", 0.9)):
        m = GradientBoostingRegressor(loss="quantile", alpha=alpha, n_estimators=200, max_depth=3,
                                      learning_rate=0.05, subsample=0.8, random_state=SEED)
        m.fit(Xtr, ytr)
        q[name] = m
    p50 = q["p50"].predict(Xte) * te["planned_days"]
    p90 = q["p90"].predict(Xte) * te["planned_days"]
    metrics["voyage_delay"] = {
        "auc": round(roc_auc_score(te["delayed"], p), 3),
        "brier": round(brier_score_loss(te["delayed"], p), 4),
        "base_rate": round(float(te["delayed"].mean()), 3),
        "p90_coverage": round(float((te["delay_days"] <= p90).mean()), 3),
        "mae_days_p50": round(mean_absolute_error(te["delay_days"], np.maximum(p50, 0)), 3),
        "n_train": len(tr), "n_test": len(te), "split": "time-based 80/20",
    }
    joblib.dump({"clf": clf, "q50": q["p50"], "q90": q["p90"], "features": VOYAGE_FEATURES}, MODELS_DIR / "voyage_risk.joblib")


def train_inventory():
    df = pd.read_csv(DATA_DIR / "inventory_consumption.csv", parse_dates=["date"])
    df["month_sin"] = np.sin(2 * np.pi * df["date"].dt.month / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["date"].dt.month / 12)
    bundle, res = {}, {}
    for item in INVENTORY_ITEMS:
        d = df[df["item"] == item].sort_values("date")
        clean = d[d["is_anomaly"] == 0]
        k = int(len(clean) * 0.8)
        tr, te = clean.iloc[:k], clean.iloc[k:]
        m = GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, random_state=SEED)
        m.fit(tr[INVENTORY_FEATURES], tr["consumption"])
        pred = m.predict(te[INVENTORY_FEATURES])
        rel_res = (te["consumption"] - pred) / np.maximum(pred, 1e-6)
        sigma = float(rel_res.std())
        mape = float(np.mean(np.abs(te["consumption"] - pred) / te["consumption"]))
        # anomaly detection check on full series (incl. injected anomalies)
        full_pred = m.predict(d[INVENTORY_FEATURES])
        z = (d["consumption"] - full_pred) / np.maximum(full_pred, 1e-6) / sigma
        flagged = z > 3.5
        res[item] = {"mape": round(mape, 3), "rel_sigma": round(sigma, 3),
                     "anomaly_precision": round(float((d["is_anomaly"][flagged]).mean()) if flagged.any() else 0, 3),
                     "anomaly_recall": round(float(flagged[d["is_anomaly"] == 1].mean()), 3)}
        bundle[item] = {"model": m, "rel_sigma": sigma}
    metrics["inventory"] = res
    joblib.dump({"items": bundle, "features": INVENTORY_FEATURES}, MODELS_DIR / "inventory_forecast.joblib")


def train_assets():
    df = pd.read_csv(DATA_DIR / "asset_telemetry.csv")
    df["type_code"] = df["asset_type"].map({t: i for i, t in enumerate(ASSET_TYPES)})
    tr, te = time_split(df, "month_index")
    clf = RandomForestClassifier(n_estimators=300, max_depth=8, min_samples_leaf=5, class_weight="balanced", random_state=SEED)
    clf.fit(tr[ASSET_FEATURES], tr["fault_next_30d"])
    p = clf.predict_proba(te[ASSET_FEATURES])[:, 1]
    metrics["asset_failure"] = {"auc": round(roc_auc_score(te["fault_next_30d"], p), 3),
                                "base_rate": round(float(te["fault_next_30d"].mean()), 3),
                                "n_train": len(tr), "n_test": len(te)}
    medians = df.groupby("asset_type")[ASSET_FEATURES[1:]].median().round(3).to_dict("index")
    joblib.dump({"clf": clf, "features": ASSET_FEATURES, "type_medians": medians}, MODELS_DIR / "asset_failure.joblib")


def train_sos():
    df = pd.read_csv(DATA_DIR / "sos_reports.csv")
    tr = df.sample(frac=0.8, random_state=SEED)
    te = df.drop(tr.index)
    out, models = {}, {}
    for target in ("incident_type", "severity"):
        pipe = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True),
                             LogisticRegression(max_iter=1000, C=8, class_weight="balanced"))
        pipe.fit(tr["text"], tr[target])
        pred = pipe.predict(te["text"])
        out[target] = {"accuracy": round(accuracy_score(te[target], pred), 3),
                       "macro_f1": round(f1_score(te[target], pred, average="macro"), 3)}
        models[target] = pipe
    metrics["sos_triage"] = out
    joblib.dump(models, MODELS_DIR / "sos_triage.joblib")


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if not (DATA_DIR / "voyage_history.csv").exists():
        from .generate_synthetic import main as gen
        gen()
    t = time.time()
    for fn in (train_voyage, train_inventory, train_assets, train_sos):
        fn()
        print(f"trained {fn.__name__[6:]:10s} ({time.time() - t:.1f}s)")
    metrics["meta"] = {"data": "synthetic", "seed": SEED, "trained_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    (MODELS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
