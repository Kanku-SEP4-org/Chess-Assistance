# Angriness labelling — sensitivity analysis

Reproduce: `python analysis/contamination_sensitivity.py` (reads the existing
`data/processed/*` splits; writes `analysis/contamination_sensitivity.json`; does **not**
touch `models/` or the shipped pipeline). Run from the trainer root.

## TL;DR
- The review called `IsolationForest(contamination=0.03)` (`steps/3_train.py:72`) an
  unjustified magic number whose change would "produce completely different labels."
- **That is false here.** `contamination` is mathematically **inert** in this pipeline — it
  cannot change the labels, the Random Forest, or any evaluation metric. It only moves the
  cosmetic `n_anomalies` count logged in `metrics.json`.
- The parameter that *actually* defines the angriness levels is **`PERCENTILE_EDGES`**. A
  sensitivity sweep over candidate edge schemes shows the shipped baseline
  `[0,10,35,65,90,100]` is **the best of the candidates on the non-circular external-validity
  signal** — so the current binning is justified, not arbitrary.

## Why contamination is inert (the math)
Labels are assigned from **percentiles of the IsolationForest `decision_function` scores**
(`3_train.py:81-88`), and in scikit-learn:

```
decision_function(X) = score_samples(X) − offset_
```

Only `offset_` depends on `contamination`; `score_samples` does not. `offset_` is a single
constant, and a constant shift cancels in a percentile comparison:

```
score_i ≤ edge_p   ⟺   (score_i − c) ≤ (edge_p − c)
```

Both the scores and the percentile edges shift by the same `c`, so every sample lands in the
same bin regardless of `contamination`. Evaluation is invariant for the same reason
(`4_evaluate.py:119-120`), and inference uses the Random Forest directly — the IsolationForest
is never consulted at inference. `contamination` only changes `predict() == -1`, i.e. the
reported `n_anomalies`/`anomaly_rate`.

## Sweep A — contamination is inert (empirical proof)
IF held at `n_estimators=200, max_features=0.75, random_state=42`; binning = baseline edges.

| contamination | n_anomalies | anomaly_rate | label_agreement vs 0.03 | rf_train_acc | val_acc | test_acc | Spearman(next Δelo) |
|---|---|---|---|---|---|---|---|
| auto | 4469 | 0.307 | **1.0** | 0.743 | 0.7262 | 0.7081 | −0.0867 |
| 0.01 | 146 | 0.010 | **1.0** | 0.743 | 0.7262 | 0.7081 | −0.0867 |
| 0.02 | 292 | 0.020 | **1.0** | 0.743 | 0.7262 | 0.7081 | −0.0867 |
| 0.03 | 437 | 0.030 | **1.0** | 0.743 | 0.7262 | 0.7081 | −0.0867 |
| 0.05 | 728 | 0.050 | **1.0** | 0.743 | 0.7262 | 0.7081 | −0.0867 |
| 0.10 | 1456 | 0.100 | **1.0** | 0.743 | 0.7262 | 0.7081 | −0.0867 |

Every label set is identical to the `0.03` baseline (100% agreement) and every metric is
identical. Only `n_anomalies` changes. **Claim proven.**

## Sweep B — the real knob: `PERCENTILE_EDGES`
contamination fixed at 0.03; each scheme regenerates labels, retrains the RF, and is evaluated.

| edge scheme | rf_train_acc | val_acc | test_acc | acc_gap | \|external-validity ρ\| | acc_gap<0.05 | tilt checks |
|---|---|---|---|---|---|---|---|
| **baseline 10/25/30/25/10** `[0,10,35,65,90,100]` | 0.743 | 0.7262 | 0.7081 | 0.018 | **0.0867** | ✓ | ✓ |
| uniform 20-each `[0,20,40,60,80,100]` | 0.719 | 0.6933 | 0.6921 | 0.001 | 0.0728 | ✓ | ✓ |
| tail-light 5/20/50/20/5 `[0,5,25,75,95,100]` | 0.796 | 0.7559 | 0.7495 | 0.006 | 0.0787 | ✓ | ✓ |
| tail-heavy 15/25/20/25/15 `[0,15,40,60,85,100]` | 0.744 | 0.7262 | 0.7172 | 0.009 | 0.0722 | ✓ | ✓ |

All schemes generalize (acc gap < 5%) and pass the tilt sanity checks. The **baseline edges
have the strongest external validity** (|ρ| = 0.0867 vs the player's next-game rating change).

Note on accuracy: `tail-light` shows a higher *accuracy* (0.7495), but that accuracy is measured
against the IsolationForest's own labels — wider, more separated extreme bins are mechanically
easier to reproduce, so it is partly circular. The honest, non-circular discriminator is the
external-validity Spearman, where the baseline wins. That is why baseline is selected.

## Conclusions / recommended framing
1. **`contamination=0.03` is not a tuned anomaly rate** in this design and does not affect the
   model — it should be documented as such (or set to `"auto"`). The notes/metrics that imply it
   controls the label rate are misleading.
2. **The angriness levels are defined by `PERCENTILE_EDGES`**, and the shipped
   `[0,10,35,65,90,100]` is empirically justified — best external validity among the candidates,
   with a small val/test gap and passing tilt checks.
3. Minor (now fixed): the logged `rf_min_samples_leaf` in `3_train.py` was `5` while the actual
   RF uses `9` (`3_train.py:101`); the logged value has been corrected to `9`. `models/metrics.json`
   (gitignored) will reflect it on the next pipeline run.

Artifact: full numbers in `analysis/contamination_sensitivity.json`.
