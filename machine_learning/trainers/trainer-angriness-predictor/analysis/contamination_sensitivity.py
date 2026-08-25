"""
Sensitivity analysis for the angriness trainer's labelling hyperparameters.

Motivation
----------
The code review flags `IsolationForest(contamination=0.03)` (steps/3_train.py) as an
unjustified magic number, claiming that changing it "produces completely different
training labels". This script tests that claim empirically and finds the opposite:

    decision_function(X) = score_samples(X) - offset_

and only `offset_` depends on `contamination` (it is a single constant). The angriness
labels are assigned by PERCENTILE bins of decision_function scores, and a constant shift
cancels in a percentile comparison:

    score_i <= edge_p   <=>   (score_i - c) <= (edge_p - c)

So `contamination` cannot change the surrogate labels, the Random Forest, or any eval
metric -- it only moves the cosmetic `n_anomalies` count. Sweep A proves this. The
parameter that ACTUALLY drives the labels is PERCENTILE_EDGES, so Sweep B runs the real
sensitivity analysis there, scored by the existing non-circular external-validity signal
(Spearman of angriness vs the player's NEXT-game rating change).

This is an OFFLINE analysis: it reads the already-produced processed splits and never
writes to models/ or touches the shipped pipeline.

Run from the trainer dir:  python analysis/contamination_sensitivity.py
"""

import importlib.util
import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier

# --- Locate trainer root (parent of this analysis/ dir) and run from there ---
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TRAINER_ROOT = os.path.dirname(THIS_DIR)
os.chdir(TRAINER_ROOT)

STEPS_DIR = os.path.join(TRAINER_ROOT, "steps")
PROCESSED_DIR = os.path.join("data", "processed")
OUT_JSON = os.path.join("analysis", "contamination_sensitivity.json")

# IF hyperparameters held fixed across the whole study (match steps/3_train.py).
IF_N_ESTIMATORS = 200
IF_MAX_FEATURES = 0.75
RANDOM_STATE = 42

# Baseline binning used by the shipped pipeline.
BASELINE_EDGES = [0, 10, 35, 65, 90, 100]

CONTAMINATION_GRID = ["auto", 0.01, 0.02, 0.03, 0.05, 0.10]

# Candidate percentile-edge schemes for the real sensitivity sweep (Sweep B).
EDGE_CANDIDATES = {
    "baseline_10_25_30_25_10": [0, 10, 35, 65, 90, 100],
    "uniform_20_each": [0, 20, 40, 60, 80, 100],
    "tail_light_5_20_50_20_5": [0, 5, 25, 75, 95, 100],
    "tail_heavy_15_25_20_25_15": [0, 15, 40, 60, 85, 100],
}


def _load_module(name, filename):
    """Import a step file whose name starts with a digit (not a valid module name)."""
    spec = importlib.util.spec_from_file_location(name, os.path.join(STEPS_DIR, filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Reuse the REAL pipeline helpers so the harness cannot drift from production code.
_train = _load_module("step3_train", "3_train.py")
_eval = _load_module("step4_evaluate", "4_evaluate.py")

IF_FEATURES = _train.IF_FEATURES
score_to_angriness = _train.score_to_angriness
build_next_game_signal = _eval.build_next_game_signal
compute_external_validity = _eval.compute_external_validity
evaluate_split = _eval.evaluate_split


def _read(split):
    return pd.read_csv(os.path.join(PROCESSED_DIR, f"{split}.csv"))


def _fit_if(features_train, contamination):
    model = IsolationForest(
        contamination=contamination,
        n_estimators=IF_N_ESTIMATORS,
        max_features=IF_MAX_FEATURES,
        random_state=RANDOM_STATE,
    )
    model.fit(features_train[IF_FEATURES].values)
    return model


def _make_labels(if_model, features_train, edges):
    scores = if_model.decision_function(features_train[IF_FEATURES].values)
    bin_edges = [float(np.percentile(scores, p)) for p in edges]
    y = np.array([score_to_angriness(s, bin_edges) for s in scores])
    return y, bin_edges


def _train_rf(raw_train, y_train):
    rf = RandomForestClassifier(
        n_estimators=200,
        random_state=RANDOM_STATE,
        max_depth=9,
        min_samples_leaf=9,
        max_features="sqrt",
        min_samples_split=10,
        n_jobs=-1,
    )
    rf.fit(raw_train[IF_FEATURES].values, y_train)
    return rf


def _evaluate(rf, if_model, bin_edges, splits, next_game_map):
    """Return val/test accuracy + test external-validity rho using the real eval helper."""
    out = {}
    for name in ("val", "test"):
        res = evaluate_split(
            name,
            splits[f"features_{name}"],
            splits[f"raw_{name}"],
            rf,
            bin_edges,
            is_supervised=True,
            if_model=if_model,
            if_features=IF_FEATURES,
            next_game_map=next_game_map,
        )
        out[name] = res
    val_acc = out["val"]["accuracy"]
    test_acc = out["test"]["accuracy"]
    ext = out["test"].get("external_validity") or {}
    rho = ext.get("spearman_next_elo_diff", {}).get("rho")
    return val_acc, test_acc, rho, out["test"]


def main():
    print(f"Trainer root: {TRAINER_ROOT}")
    splits = {
        "features_train": _read("features_train"),
        "raw_train": _read("raw_train"),
        "features_val": _read("features_val"),
        "raw_val": _read("raw_val"),
        "features_test": _read("features_test"),
        "raw_test": _read("raw_test"),
    }
    next_game_map = build_next_game_signal()
    print(f"Next-game signal pairs: {len(next_game_map) if next_game_map else 0}")

    ft = splits["features_train"]
    rt = splits["raw_train"]

    # ---------- Sweep A: contamination (expected: inert) ----------
    print("\n" + "=" * 78)
    print("SWEEP A - contamination (binning = baseline percentile edges, all else fixed)")
    print("=" * 78)

    baseline_labels = None
    sweep_a = []
    for cont in CONTAMINATION_GRID:
        if_model = _fit_if(ft, cont)
        preds = if_model.predict(ft[IF_FEATURES].values)
        n_anom = int((preds == -1).sum())
        y, bin_edges = _make_labels(if_model, ft, BASELINE_EDGES)
        if cont == 0.03:
            baseline_labels = y
        rf = _train_rf(rt, y)
        rf_train_acc = float((rf.predict(rt[IF_FEATURES].values) == y).mean())
        val_acc, test_acc, rho, _ = _evaluate(rf, if_model, bin_edges, splits, next_game_map)
        sweep_a.append({
            "contamination": cont,
            "n_anomalies": n_anom,
            "anomaly_rate": round(n_anom / len(ft), 4),
            "rf_train_accuracy": round(rf_train_acc, 4),
            "val_accuracy": val_acc,
            "test_accuracy": test_acc,
            "spearman_next_elo_diff": rho,
            "_labels": y,
        })

    # label agreement vs the 0.03 baseline
    for row in sweep_a:
        row["label_agreement_vs_0.03"] = round(float((row.pop("_labels") == baseline_labels).mean()), 6)

    cols = ["contamination", "n_anomalies", "anomaly_rate", "label_agreement_vs_0.03",
            "rf_train_accuracy", "val_accuracy", "test_accuracy", "spearman_next_elo_diff"]
    print("\n" + "  ".join(f"{c:>22}" for c in cols))
    for row in sweep_a:
        print("  ".join(f"{str(row[c]):>22}" for c in cols))

    all_inert = all(r["label_agreement_vs_0.03"] == 1.0 for r in sweep_a)
    print(f"\n>>> contamination is INERT (all label_agreement == 1.0): {all_inert}")

    # ---------- Sweep B: percentile edges (the real knob) ----------
    print("\n" + "=" * 78)
    print("SWEEP B - PERCENTILE_EDGES (contamination fixed at 0.03)")
    print("=" * 78)

    if_model = _fit_if(ft, 0.03)
    sweep_b = []
    for label, edges in EDGE_CANDIDATES.items():
        y, bin_edges = _make_labels(if_model, ft, edges)
        rf = _train_rf(rt, y)
        rf_train_acc = float((rf.predict(rt[IF_FEATURES].values) == y).mean())
        val_acc, test_acc, rho, test_res = _evaluate(rf, if_model, bin_edges, splits, next_game_map)
        acc_gap = round(val_acc - test_acc, 4)
        # tilt check: do tilted levels (4,5) show higher ACPL/blunders/consec-losses than calm (1,2)?
        per = test_res["per_level"]

        def wmean(levels, col):
            tot = sum(per.get(lv, {}).get("count", 0) for lv in levels)
            if tot == 0:
                return 0.0
            # mean_* is None for empty levels; treat as 0 (its count is 0 so it contributes nothing).
            return sum((per.get(lv, {}).get(f"mean_{col}") or 0) * per.get(lv, {}).get("count", 0)
                       for lv in levels) / tot

        tilt_ok = all(
            wmean(["4", "5"], c) > wmean(["1", "2"], c)
            for c in ["acpl_player", "blunder_cnt_player", "consecutive_losses_pregame"]
        )
        sweep_b.append({
            "edges_name": label,
            "edges": edges,
            "rf_train_accuracy": round(rf_train_acc, 4),
            "val_accuracy": val_acc,
            "test_accuracy": test_acc,
            "accuracy_gap_val_test": acc_gap,
            "abs_external_validity_rho": round(abs(rho), 4) if rho is not None else None,
            "external_validity_rho": rho,
            "acc_gap_ok": bool(abs(acc_gap) < 0.05),
            "tilt_checks_pass": bool(tilt_ok),
        })

    bcols = ["edges_name", "rf_train_accuracy", "val_accuracy", "test_accuracy",
             "accuracy_gap_val_test", "abs_external_validity_rho", "acc_gap_ok", "tilt_checks_pass"]
    print("\n" + "  ".join(f"{c:>24}" for c in bcols))
    for row in sweep_b:
        print("  ".join(f"{str(row[c]):>24}" for c in bcols))

    # Rank eligible schemes by external validity (higher |rho| = stronger tilt signal).
    eligible = [r for r in sweep_b if r["acc_gap_ok"] and r["tilt_checks_pass"]
                and r["abs_external_validity_rho"] is not None]
    ranked = sorted(eligible, key=lambda r: r["abs_external_validity_rho"], reverse=True)
    best = ranked[0] if ranked else None
    print(f"\n>>> Best eligible edge scheme by |external-validity rho|: "
          f"{best['edges_name'] if best else 'none eligible'}")

    report = {
        "summary": {
            "contamination_is_inert": all_inert,
            "explanation": "decision_function = score_samples - offset_; only offset_ depends on "
                           "contamination, and a constant shift cancels under percentile binning, "
                           "so labels/RF/eval are identical. Only n_anomalies (cosmetic) changes.",
            "real_label_driver": "PERCENTILE_EDGES",
            "best_edge_scheme_by_external_validity": best["edges_name"] if best else None,
            "baseline_is_competitive": (
                None if best is None
                else best["edges_name"] == "baseline_10_25_30_25_10"
            ),
        },
        "fixed_if_hyperparameters": {
            "n_estimators": IF_N_ESTIMATORS,
            "max_features": IF_MAX_FEATURES,
            "random_state": RANDOM_STATE,
        },
        "sweep_a_contamination": sweep_a,
        "sweep_b_percentile_edges": sweep_b,
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved: {OUT_JSON}")


if __name__ == "__main__":
    sys.exit(main())
