# Archived: pre-leak-fix angriness steps

These are the **previous versions** of the angriness pipeline steps, kept for history. They are
**reference only** — `run_pipeline.py` runs the live files in `steps/`, not these.

They were replaced to fix two issues (see `cannyboizs-notes/exam/angriness-predictor-defense.md`
and `notebooks/pipeline-v3.ipynb`):

1. **Train/test leakage** — preprocessing was fit on the full dataset before the split.
2. **Circular validation** — angriness was only checked against the Isolation Forest's own
   input features.

> Note: these `.py` reference relative paths (`data/processed/...`) assuming they run from the
> trainer root, so they are not runnable from inside this archive folder. They are a snapshot,
> like the sibling `steps/legacy/` and `steps/init-v1/` generations.

## What changed (this archive → current `steps/`)

| Step | Pre-fix (here) | Current (`steps/`) |
|---|---|---|
| **`2_features.py`** | Impute + IQR outlier removal + `StandardScaler.fit_transform` on the **full dataset**; emits a single `features.csv` (+ `raw_cleaned.csv`, `scaler.pkl`). The split happened later, in `3_train.py`. | **Splits first** (two-stage 64/16/20, `random_state=42`), then fits impute / IQR bounds / scaler on **train only** and applies to val/test; outliers dropped from **train only**. Emits `features_{train,val,test}.csv` + `raw_{train,val,test}.csv`. **(Fixes the leak.)** |
| **`3_train.py`** | Reads `features.csv`, **performs the split**, saves the split files, then IF → percentile bins → labels → RF. | Reads the **pre-split** `features_train.csv` / `raw_train.csv` (no split here); IF → bins → labels → RF. Split counts are read back for `metrics.json`. |
| **`4_evaluate.py`** | Surrogate accuracy / F1 vs IF labels, in-sample Spearman, per-level stats, overfitting assessment. | **Adds** `build_next_game_signal()` + `compute_external_validity()` — a **non-circular** check correlating predicted angriness with the player's **next-game** rating change (`elo_diff` of game N+1, not an IF input). Wired through `evaluate_split`; adds `external_validity_test` to the report. Everything else unchanged. |

### The leak, precisely
Only **feature statistics** (scaler mean/std, IQR cut-points) leaked — they were computed on
train+val+test. The **labels did not leak**: the Isolation Forest was always fit on the train
split only. It is a preprocessing ("soft") leak, milder than leaking the target, but still
incorrect. The current `steps/` fit every transform on train only.

## How to view the exact diff

```bash
# from the trainer root (machine_learning/trainers/trainer-angriness-predictor)
diff steps/legacy/pre-leak-fix/2_features.py steps/2_features.py
diff steps/legacy/pre-leak-fix/3_train.py    steps/3_train.py
diff steps/legacy/pre-leak-fix/4_evaluate.py steps/4_evaluate.py
# 1_gather.py is unchanged between this archive and the live pipeline.
```
