"""
Step 3: Compare unsupervised algorithms for tilt detection.

Runs K-Means, Isolation Forest, and DBSCAN on the preprocessed features.
Evaluates with silhouette score, produces PCA visualizations, and prints
cluster/anomaly summaries so you can pick the best approach.

Reference: cannyboizs-notes/angriness-predictor-feature-recommendation.md
  - K-Means + PCA for clustering "normal" vs "erratic" play
  - Anomaly detection for flagging tilt sessions

Run from trainer-angriness-predictor/:
    python steps/init/3_algorithm_comparison.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"
PLOT_DIR = Path(__file__).resolve().parent / "plots"
PLOT_DIR.mkdir(exist_ok=True)

SCALED_CSV = DATA_DIR / "features_scaled.csv"


def load_data() -> pd.DataFrame:
    if not SCALED_CSV.exists():
        raise FileNotFoundError(
            f"{SCALED_CSV} not found. Run 2_preprocess.py first.")
    return pd.read_csv(SCALED_CSV)


# ---------------------------------------------------------------------------
# PCA for visualization
# ---------------------------------------------------------------------------

def run_pca(df: pd.DataFrame, n_components: int = 2) -> np.ndarray:
    pca = PCA(n_components=n_components, random_state=42)
    reduced = pca.fit_transform(df.values)
    explained = pca.explained_variance_ratio_
    print(f"\n  PCA explained variance: {explained[0]:.2%} + {explained[1]:.2%} = {sum(explained):.2%}")
    print(f"  Top components:")
    for i, comp in enumerate(pca.components_[:2]):
        top_idx = np.argsort(np.abs(comp))[-5:][::-1]
        top_features = [(df.columns[j], comp[j]) for j in top_idx]
        print(f"    PC{i+1}: {', '.join(f'{name}({w:+.2f})' for name, w in top_features)}")
    return reduced


def plot_clusters(reduced: np.ndarray, labels: np.ndarray, title: str, filename: str):
    fig, ax = plt.subplots(figsize=(10, 7))
    scatter = ax.scatter(reduced[:, 0], reduced[:, 1],
                         c=labels, cmap="tab10", alpha=0.3, s=5)
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_title(title)
    fig.colorbar(scatter, ax=ax, label="Cluster/Label")
    fig.tight_layout()
    fig.savefig(PLOT_DIR / filename, dpi=150)
    print(f"  Saved: {PLOT_DIR / filename}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# K-Means
# ---------------------------------------------------------------------------

def run_kmeans(df: pd.DataFrame, reduced: np.ndarray):
    print("\n=== K-Means Clustering ===")

    # Elbow method
    inertias = []
    silhouettes = []
    K_range = range(2, 9)

    for k in K_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(df.values)
        inertias.append(km.inertia_)
        sil = silhouette_score(df.values, labels, sample_size=min(10000, len(df)))
        silhouettes.append(sil)
        print(f"  k={k}: inertia={km.inertia_:,.0f}, silhouette={sil:.4f}")

    # Plot elbow
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ax1.plot(list(K_range), inertias, "bo-")
    ax1.set_xlabel("k")
    ax1.set_ylabel("Inertia")
    ax1.set_title("Elbow Method")
    ax2.plot(list(K_range), silhouettes, "ro-")
    ax2.set_xlabel("k")
    ax2.set_ylabel("Silhouette Score")
    ax2.set_title("Silhouette Score vs k")
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "kmeans_elbow.png", dpi=150)
    print(f"  Saved: {PLOT_DIR / 'kmeans_elbow.png'}")
    plt.close(fig)

    # Best k by silhouette
    best_k = list(K_range)[np.argmax(silhouettes)]
    print(f"  Best k by silhouette: {best_k}")

    km_best = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    labels = km_best.fit_predict(df.values)

    plot_clusters(reduced, labels, f"K-Means (k={best_k})", "kmeans_pca.png")

    # Cluster profiles
    df_temp = df.copy()
    df_temp["cluster"] = labels
    print(f"\n  Cluster sizes: {dict(pd.Series(labels).value_counts().sort_index())}")
    print("\n  Cluster means (key tilt features):")
    tilt_cols = [c for c in ["consecutive_losses_pregame", "avg_tpm_seconds_player",
                              "blunder_cnt_player", "acpl_player", "accuracy_player"]
                 if c in df.columns]
    if tilt_cols:
        print(df_temp.groupby("cluster")[tilt_cols].mean().round(3).to_string())

    return labels, best_k


# ---------------------------------------------------------------------------
# Isolation Forest
# ---------------------------------------------------------------------------

def run_isolation_forest(df: pd.DataFrame, reduced: np.ndarray):
    print("\n=== Isolation Forest (Anomaly Detection) ===")

    results = {}
    for contamination in [0.05, 0.10, 0.15, 0.20]:
        iso = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=200,
        )
        labels = iso.fit_predict(df.values)  # 1=normal, -1=anomaly
        n_anomalies = (labels == -1).sum()
        scores = iso.decision_function(df.values)
        results[contamination] = {
            "labels": labels,
            "scores": scores,
            "n_anomalies": n_anomalies,
        }
        print(f"  contamination={contamination:.0%}: {n_anomalies} anomalies ({n_anomalies/len(df):.1%})")

    # Use 10% as default visualization
    default = results[0.10]
    is_anomaly = (default["labels"] == -1).astype(int)
    plot_clusters(reduced, is_anomaly, "Isolation Forest (10% contamination)", "iforest_pca.png")

    # Anomaly profile vs normal
    df_temp = df.copy()
    df_temp["is_anomaly"] = is_anomaly
    tilt_cols = [c for c in ["consecutive_losses_pregame", "avg_tpm_seconds_player",
                              "blunder_cnt_player", "acpl_player", "accuracy_player",
                              "avg_ppm", "avg_celsius", "water_intake_ml"]
                 if c in df.columns]
    if tilt_cols:
        print("\n  Normal vs Anomaly means (key features):")
        print(df_temp.groupby("is_anomaly")[tilt_cols].mean().round(3).to_string())

    # Score distribution
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(default["scores"], bins=80, edgecolor="white", alpha=0.8)
    ax.axvline(x=0, color="red", linestyle="--", label="threshold")
    ax.set_xlabel("Anomaly Score")
    ax.set_ylabel("Count")
    ax.set_title("Isolation Forest Score Distribution")
    ax.legend()
    fig.tight_layout()
    fig.savefig(PLOT_DIR / "iforest_scores.png", dpi=150)
    print(f"  Saved: {PLOT_DIR / 'iforest_scores.png'}")
    plt.close(fig)

    return default["labels"], default["scores"]


# ---------------------------------------------------------------------------
# DBSCAN
# ---------------------------------------------------------------------------

def run_dbscan(df: pd.DataFrame, reduced: np.ndarray):
    print("\n=== DBSCAN ===")

    # DBSCAN on PCA-reduced data (full-dimensional DBSCAN is unreliable)
    for eps in [1.0, 1.5, 2.0, 2.5]:
        db = DBSCAN(eps=eps, min_samples=10)
        labels = db.fit_predict(reduced)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        n_noise = (labels == -1).sum()
        print(f"  eps={eps}: {n_clusters} clusters, {n_noise} noise points ({n_noise/len(df):.1%})")

        if n_clusters >= 2:
            mask = labels != -1
            if mask.sum() > 1:
                sil = silhouette_score(reduced[mask], labels[mask],
                                        sample_size=min(10000, mask.sum()))
                print(f"    silhouette (excl. noise): {sil:.4f}")

    # Visualize eps=2.0 as a reasonable middle ground
    db = DBSCAN(eps=2.0, min_samples=10)
    labels = db.fit_predict(reduced)
    plot_clusters(reduced, labels, "DBSCAN (eps=2.0)", "dbscan_pca.png")

    return labels


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    df = load_data()
    print(f"Loaded {len(df)} rows, {len(df.columns)} features")

    reduced = run_pca(df)
    km_labels, best_k = run_kmeans(df, reduced)
    iso_labels, iso_scores = run_isolation_forest(df, reduced)
    db_labels = run_dbscan(df, reduced)

    print("\n" + "=" * 60)
    print("SUMMARY — Pick the approach that best separates tilt patterns:")
    print("  - K-Means: Good if clusters show clear behavioral differences")
    print("    (high ACPL/blunders in one cluster, low in another)")
    print("  - Isolation Forest: Good if tilt is rare and anomalous")
    print("    (check if anomalies have high consecutive_losses + high ACPL)")
    print("  - DBSCAN: Good if tilt forms dense pockets in feature space")
    print("=" * 60)

    print("\nAlgorithm comparison complete. Check plots/ for visualizations.")


if __name__ == "__main__":
    main()
