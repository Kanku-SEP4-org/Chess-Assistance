"""
Step 4: Hyperparameter tuning and final algorithm selection.

After reviewing the outputs of 3_algorithm_comparison.py, run this script
to fine-tune the chosen algorithm(s). It tests a grid of hyperparameters
for K-Means and Isolation Forest, evaluates with silhouette / anomaly
separation metrics, and saves the best configuration.

Run from trainer-angriness-predictor/:
    python steps/init/4_tune_and_select.py
"""

from pathlib import Path

import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"
PLOT_DIR = Path(__file__).resolve().parent / "plots"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
PLOT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

SCALED_CSV = DATA_DIR / "features_scaled.csv"
UNSCALED_CSV = DATA_DIR / "features_unscaled.csv"

TILT_FEATURES = [
    "consecutive_losses_pregame",
    "avg_tpm_seconds_player",
    "blunder_cnt_player",
    "acpl_player",
    "accuracy_player",
]


def load_data():
    if not SCALED_CSV.exists():
        raise FileNotFoundError(
            f"{SCALED_CSV} not found. Run 2_preprocess.py first.")
    scaled = pd.read_csv(SCALED_CSV)
    unscaled = pd.read_csv(UNSCALED_CSV) if UNSCALED_CSV.exists() else None
    return scaled, unscaled


# ---------------------------------------------------------------------------
# K-Means tuning
# ---------------------------------------------------------------------------

def tune_kmeans(df: pd.DataFrame):
    print("\n=== K-Means Hyperparameter Tuning ===")

    results = []
    for k in range(2, 8):
        for init_method in ["k-means++", "random"]:
            for n_init in [10, 20]:
                km = KMeans(
                    n_clusters=k,
                    init=init_method,
                    n_init=n_init,
                    max_iter=500,
                    random_state=42,
                )
                labels = km.fit_predict(df.values)
                sil = silhouette_score(
                    df.values, labels,
                    sample_size=min(10_000, len(df)),
                )
                results.append({
                    "k": k,
                    "init": init_method,
                    "n_init": n_init,
                    "silhouette": round(sil, 5),
                    "inertia": round(km.inertia_, 1),
                })
                print(f"  k={k}, init={init_method}, n_init={n_init} → "
                      f"sil={sil:.4f}, inertia={km.inertia_:,.0f}")

    results_df = pd.DataFrame(results).sort_values("silhouette", ascending=False)
    best = results_df.iloc[0]
    print(f"\n  Best K-Means config:")
    print(f"    k={int(best['k'])}, init={best['init']}, n_init={int(best['n_init'])}")
    print(f"    silhouette={best['silhouette']:.5f}")

    results_df.to_csv(OUTPUT_DIR / "kmeans_tuning.csv", index=False)
    print(f"  Saved: {OUTPUT_DIR / 'kmeans_tuning.csv'}")

    return results_df, best


# ---------------------------------------------------------------------------
# Isolation Forest tuning
# ---------------------------------------------------------------------------

def tune_isolation_forest(df: pd.DataFrame, unscaled: pd.DataFrame | None):
    print("\n=== Isolation Forest Hyperparameter Tuning ===")

    tilt_cols = [c for c in TILT_FEATURES if c in df.columns]
    results = []

    for contamination in [0.03, 0.05, 0.08, 0.10, 0.15, 0.20]:
        for n_estimators in [100, 200, 300]:
            for max_features in [0.5, 0.75, 1.0]:
                iso = IsolationForest(
                    contamination=contamination,
                    n_estimators=n_estimators,
                    max_features=max_features,
                    random_state=42,
                )
                labels = iso.fit_predict(df.values)
                scores = iso.decision_function(df.values)

                n_anomalies = (labels == -1).sum()
                anomaly_ratio = n_anomalies / len(df)

                score_sep = 0.0
                if tilt_cols and unscaled is not None:
                    normal_mask = labels == 1
                    anomaly_mask = labels == -1
                    if anomaly_mask.sum() > 0:
                        normal_means = unscaled.loc[normal_mask, tilt_cols].mean()
                        anomaly_means = unscaled.loc[anomaly_mask, tilt_cols].mean()
                        diffs = {}
                        for col in tilt_cols:
                            if col == "accuracy_player":
                                diffs[col] = normal_means[col] - anomaly_means[col]
                            else:
                                diffs[col] = anomaly_means[col] - normal_means[col]
                        score_sep = np.mean(list(diffs.values()))

                results.append({
                    "contamination": contamination,
                    "n_estimators": n_estimators,
                    "max_features": max_features,
                    "n_anomalies": n_anomalies,
                    "anomaly_ratio": round(anomaly_ratio, 4),
                    "tilt_separation": round(score_sep, 4),
                    "mean_anomaly_score": round(float(scores[labels == -1].mean()), 4) if n_anomalies > 0 else 0,
                    "mean_normal_score": round(float(scores[labels == 1].mean()), 4),
                })

    results_df = pd.DataFrame(results).sort_values(
        "tilt_separation", ascending=False)

    print("\n  Top 5 configs by tilt feature separation:")
    print(results_df.head(5).to_string(index=False))

    results_df.to_csv(OUTPUT_DIR / "iforest_tuning.csv", index=False)
    print(f"\n  Saved: {OUTPUT_DIR / 'iforest_tuning.csv'}")

    return results_df


# ---------------------------------------------------------------------------
# Final model profile
# ---------------------------------------------------------------------------

def profile_best_model(df: pd.DataFrame, unscaled: pd.DataFrame | None,
                       km_best: pd.Series, iso_df: pd.DataFrame):
    print("\n" + "=" * 60)
    print("FINAL PROFILE — Best configurations")
    print("=" * 60)

    best_k = int(km_best["k"])
    km = KMeans(
        n_clusters=best_k,
        init=km_best["init"],
        n_init=int(km_best["n_init"]),
        max_iter=500,
        random_state=42,
    )
    km_labels = km.fit_predict(df.values)

    print(f"\n--- K-Means (k={best_k}) ---")
    print(f"  Cluster sizes: {dict(pd.Series(km_labels).value_counts().sort_index())}")

    if unscaled is not None:
        tilt_cols = [c for c in TILT_FEATURES if c in unscaled.columns]
        if tilt_cols:
            profile = unscaled.copy()
            profile["cluster"] = km_labels
            print("\n  Cluster means (unscaled):")
            print(profile.groupby("cluster")[tilt_cols].mean().round(2).to_string())

    iso_best = iso_df.iloc[0]
    iso = IsolationForest(
        contamination=iso_best["contamination"],
        n_estimators=int(iso_best["n_estimators"]),
        max_features=iso_best["max_features"],
        random_state=42,
    )
    iso_labels = iso.fit_predict(df.values)

    print(f"\n--- Isolation Forest (contamination={iso_best['contamination']}) ---")
    print(f"  Anomalies: {(iso_labels == -1).sum()} / {len(df)}")

    if unscaled is not None:
        tilt_cols = [c for c in TILT_FEATURES if c in unscaled.columns]
        if tilt_cols:
            profile = unscaled.copy()
            profile["is_anomaly"] = (iso_labels == -1).astype(int)
            print("\n  Normal vs Anomaly means (unscaled):")
            print(profile.groupby("is_anomaly")[tilt_cols].mean().round(2).to_string())

    # PCA visualization of both
    pca = PCA(n_components=2, random_state=42)
    reduced = pca.fit_transform(df.values)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    scatter1 = ax1.scatter(reduced[:, 0], reduced[:, 1],
                           c=km_labels, cmap="tab10", alpha=0.3, s=5)
    ax1.set_xlabel("PC1")
    ax1.set_ylabel("PC2")
    ax1.set_title(f"K-Means (k={best_k})")
    fig.colorbar(scatter1, ax=ax1, label="Cluster")

    iso_colors = (iso_labels == -1).astype(int)
    scatter2 = ax2.scatter(reduced[:, 0], reduced[:, 1],
                           c=iso_colors, cmap="RdYlGn_r", alpha=0.3, s=5)
    ax2.set_xlabel("PC1")
    ax2.set_ylabel("PC2")
    ax2.set_title(f"Isolation Forest (c={iso_best['contamination']})")
    fig.colorbar(scatter2, ax=ax2, label="Anomaly")

    fig.suptitle("Best Configurations — Side by Side", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(PLOT_DIR / "best_models_pca.png", dpi=150)
    print(f"\n  Saved: {PLOT_DIR / 'best_models_pca.png'}")
    plt.close(fig)

    # Save config
    config = {
        "kmeans": {
            "k": best_k,
            "init": km_best["init"],
            "n_init": int(km_best["n_init"]),
            "silhouette": float(km_best["silhouette"]),
        },
        "isolation_forest": {
            "contamination": float(iso_best["contamination"]),
            "n_estimators": int(iso_best["n_estimators"]),
            "max_features": float(iso_best["max_features"]),
            "tilt_separation": float(iso_best["tilt_separation"]),
        },
    }
    config_path = OUTPUT_DIR / "best_config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"  Saved: {config_path}")

    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("  1. Review cluster profiles — does one cluster show clear tilt?")
    print("  2. Review anomaly profiles — do anomalies have high ACPL/blunders?")
    print("  3. Pick the approach and build production steps/ pipeline")
    print("  4. Consider: K-Means labels → supervised classifier (RandomForest)")
    print("     or Isolation Forest anomaly score → angriness scale (1-10)")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    scaled, unscaled = load_data()
    print(f"Loaded {len(scaled)} rows, {len(scaled.columns)} features")

    km_results, km_best = tune_kmeans(scaled)
    iso_results = tune_isolation_forest(scaled, unscaled)
    profile_best_model(scaled, unscaled, km_best, iso_results)

    print("\nTuning complete. Check output/ and plots/ for results.")


if __name__ == "__main__":
    main()
