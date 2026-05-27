import json
import os

import joblib
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import accuracy_score, f1_score

PROCESSED_DIR = os.path.join("data", "processed")
MODEL_PATH = os.getenv("MODEL_PATH", "models/model.pkl")
IF_MODEL_PATH = os.getenv("IF_MODEL_PATH", "models/if_model.pkl")
BINS_PATH = os.getenv("BINS_PATH", "models/angriness_bins.json")
OUT_PATH = os.getenv("EVAL_METRICS_PATH", "models/eval_metrics.json")

SPLITS = {
    "train": {
        "features": os.path.join(PROCESSED_DIR, "features_train.csv"),
        "raw": os.path.join(PROCESSED_DIR, "raw_train.csv"),
    },
    "val": {
        "features": os.path.join(PROCESSED_DIR, "features_val.csv"),
        "raw": os.path.join(PROCESSED_DIR, "raw_val.csv"),
    },
    "test": {
        "features": os.path.join(PROCESSED_DIR, "features_test.csv"),
        "raw": os.path.join(PROCESSED_DIR, "raw_test.csv"),
    },
}

TILT_FEATURES = [
    "acpl_player", "blunder_cnt_player", "mistake_cnt_player",
    "inaccuracy_cnt_player", "consecutive_losses_pregame",
    "accuracy_player", "avg_tpm_seconds_player",
]

COMPOSITE_COLS = ["acpl_player", "blunder_cnt_player", "consecutive_losses_pregame"]

ACC_GAP_THRESHOLD = 0.05
SPEARMAN_GAP_THRESHOLD = 0.10


def score_to_angriness(score: float, bin_edges: list[float]) -> int:
    for i in range(len(bin_edges) - 1):
        if score <= bin_edges[i + 1]:
            return 5 - i
    return 1


def evaluate_split(name, features_df, raw_df, model, bin_edges, is_supervised,
                   if_model=None, if_features=None):
    if is_supervised:
        # RF trained on unscaled features — predict using raw data
        angriness = model.predict(raw_df[if_features].values)
        # IF labels from scaled features for accuracy comparison
        if_scores = if_model.decision_function(features_df[if_features].values)
        y_true = np.array([score_to_angriness(s, bin_edges) for s in if_scores])
        acc = round(float(accuracy_score(y_true, angriness)), 4)
        f1 = round(float(f1_score(y_true, angriness, average="weighted")), 4)
    else:
        scores = model.decision_function(features_df.values)
        angriness = np.array([score_to_angriness(s, bin_edges) for s in scores])
        acc = None
        f1 = None

    angriness_dist = {
        str(level): int((angriness == level).sum()) for level in range(1, 6)
    }

    spearman_results = {}
    for col in COMPOSITE_COLS:
        if col in raw_df.columns:
            corr, pval = spearmanr(angriness.astype(float), raw_df[col].values)
            spearman_results[col] = {
                "rho": round(float(corr), 4),
                "p_value": round(float(pval), 6),
            }

    available_tilt = [c for c in TILT_FEATURES if c in raw_df.columns]
    raw_df = raw_df.copy()
    raw_df["_angriness"] = angriness

    per_level = {}
    for level in range(1, 6):
        mask = raw_df["_angriness"] == level
        subset = raw_df.loc[mask]
        stats = {"count": int(mask.sum())}
        for col in available_tilt:
            stats[f"mean_{col}"] = round(float(subset[col].mean()), 2) if len(subset) > 0 else None
        per_level[str(level)] = stats

    result = {
        "n_rows": len(raw_df),
        "spearman": spearman_results,
        "angriness_distribution": angriness_dist,
        "per_level": per_level,
    }
    if is_supervised:
        result["accuracy"] = acc
        result["f1_weighted"] = f1

    return result


def compute_overfitting_assessment(split_results, is_supervised):
    train = split_results["train"]
    val = split_results["val"]
    test = split_results["test"]

    gaps = {}
    reasons = []
    notes = [
        "Training Accuracy of 1.0000 is expected: RF memorizes training data (unconstrained tree depth)",
        "Model serves as Surrogate to Stage 1 Isolation Forest",
    ]

    if is_supervised:
        acc_gap = round(val["accuracy"] - test["accuracy"], 4)
        gaps["accuracy_gap_val_test"] = acc_gap
        notes.append(
            f"Strong generalization: Val ({val['accuracy']}) vs Test ({test['accuracy']}) gap = {abs(acc_gap):.4f}"
        )
        if abs(acc_gap) > ACC_GAP_THRESHOLD:
            reasons.append(
                f"Accuracy gap (val vs test) = {acc_gap:.4f} (val {val['accuracy']:.4f} vs test {test['accuracy']:.4f})"
            )

    spearman_gaps = {}
    for col in COMPOSITE_COLS:
        tr = train["spearman"].get(col, {}).get("rho", 0)
        te = test["spearman"].get(col, {}).get("rho", 0)
        spearman_gaps[col] = round(abs(tr - te), 4)
        if spearman_gaps[col] > SPEARMAN_GAP_THRESHOLD:
            reasons.append(f"Spearman gap for {col} = {spearman_gaps[col]:.4f}")

    gaps["spearman_gaps"] = spearman_gaps

    return {
        **gaps,
        "is_overfitting": len(reasons) > 0,
        "reasons": reasons,
        "notes": notes,
    }


def print_comparison(split_results, assessment, is_supervised):
    short = {"acpl_player": "ACPL", "blunder_cnt_player": "Blunders", "consecutive_losses_pregame": "ConsLoss"}
    cols = list(short.keys())

    print("\n=== Surrogate Model Generalization Assessment ===\n")
    header = f"{'Split':>6}  {'N':>6}"
    if is_supervised:
        header += f"  {'Accuracy':>8}  {'F1':>6}"
    for col in cols:
        header += f"  {short[col] + ' rho':>12}"
    print(header)
    print("-" * len(header))

    for name in ["train", "val", "test"]:
        r = split_results[name]
        row = f"{name:>6}  {r['n_rows']:>6}"
        if is_supervised:
            row += f"  {r['accuracy']:>8.4f}  {r['f1_weighted']:>6.4f}"
        for col in cols:
            rho = r["spearman"].get(col, {}).get("rho", "-")
            if isinstance(rho, float):
                row += f"  {rho:>12.4f}"
            else:
                row += f"  {rho:>12}"
        print(row)

    print(f"\n{'=' * 50}")
    if assessment["is_overfitting"]:
        print("POSSIBLE GENERALIZATION ISSUES:")
        for reason in assessment["reasons"]:
            print(f"  - {reason}")
    else:
        print("SURROGATE MODEL ASSESSMENT:")
        for note in assessment.get("notes", []):
            print(f"  - {note}")
        if is_supervised:
            print(f"  Accuracy gap (val vs test): {assessment.get('accuracy_gap_val_test', 0):.4f} (threshold: {ACC_GAP_THRESHOLD})")


def print_test_details(split_results):
    test = split_results["test"]

    per_level = test["per_level"]
    calm_levels = ["1", "2"]
    tilted_levels = ["4", "5"]

    def weighted_mean(levels, col):
        total_count = sum(per_level.get(lv, {}).get("count", 0) for lv in levels)
        if total_count == 0:
            return 0
        return sum(
            per_level.get(lv, {}).get(f"mean_{col}", 0) * per_level.get(lv, {}).get("count", 0)
            for lv in levels
        ) / total_count

    checks = {
        "acpl_higher_when_tilted": weighted_mean(tilted_levels, "acpl_player") > weighted_mean(calm_levels, "acpl_player"),
        "blunders_higher_when_tilted": weighted_mean(tilted_levels, "blunder_cnt_player") > weighted_mean(calm_levels, "blunder_cnt_player"),
        "consecutive_losses_higher_when_tilted": weighted_mean(tilted_levels, "consecutive_losses_pregame") > weighted_mean(calm_levels, "consecutive_losses_pregame"),
    }
    validations = {k: bool(v) for k, v in checks.items()}
    validations["all_passed"] = all(validations.values())

    status = "PASS" if validations["all_passed"] else "FAIL"
    print(f"\n  Validation ({status}):")
    for check, result in validations.items():
        if check != "all_passed":
            print(f"    {check}: {'PASS' if result else 'FAIL'}")

    print(f"\n  Test set per-level stats:")
    print(f"  {'Level':>5}  {'Count':>6}  {'ACPL':>6}  {'Blunders':>8}  {'ConsLoss':>8}")
    for level in range(1, 6):
        s = per_level.get(str(level), {})
        acpl = s.get("mean_acpl_player", "-")
        blunders = s.get("mean_blunder_cnt_player", "-")
        cons = s.get("mean_consecutive_losses_pregame", "-")
        print(f"  {level:>5}  {s.get('count', 0):>6}  {acpl:>6}  {blunders:>8}  {cons:>8}")

    return validations


def main():
    for path, name in [(MODEL_PATH, "model"), (BINS_PATH, "bins")]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing {name}: {path}")

    model = joblib.load(MODEL_PATH)
    with open(BINS_PATH) as f:
        bins_data = json.load(f)
    bin_edges = bins_data["bin_edges"]
    is_supervised = bins_data.get("supervised", False)
    if_features = bins_data.get("if_features")

    if_model = None
    if is_supervised:
        print(f"Model type: {bins_data.get('model_type', 'unknown')} (supervised)")
        if os.path.exists(IF_MODEL_PATH):
            if_model = joblib.load(IF_MODEL_PATH)
        else:
            raise FileNotFoundError(f"Supervised model requires IF model for label generation: {IF_MODEL_PATH}")
    else:
        print("Model type: Isolation Forest (unsupervised)")

    split_results = {}
    for name, paths in SPLITS.items():
        if not os.path.exists(paths["features"]):
            raise FileNotFoundError(f"Missing {name} features: {paths['features']}")
        if not os.path.exists(paths["raw"]):
            raise FileNotFoundError(f"Missing {name} raw data: {paths['raw']}")

        features_df = pd.read_csv(paths["features"])
        raw_df = pd.read_csv(paths["raw"])

        split_results[name] = evaluate_split(
            name, features_df, raw_df, model, bin_edges, is_supervised,
            if_model=if_model, if_features=if_features,
        )

    assessment = compute_overfitting_assessment(split_results, is_supervised)

    print("Evaluation complete.")
    print_comparison(split_results, assessment, is_supervised)
    validations = print_test_details(split_results)

    report = {
        "model_type": bins_data.get("model_type", "isolation_forest"),
        "supervised": is_supervised,
        "splits": split_results,
        "overfitting_assessment": assessment,
        "validations": validations,
    }

    os.makedirs(os.path.dirname(OUT_PATH) or ".", exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
