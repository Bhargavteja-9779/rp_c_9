# Iteration log (Phase 19): method changes made after inspecting results

Every change made after seeing results is listed here with its hypothesis and evidence. Superseded versions remain in the results: rows labelled `(v1)` in `results/raw_results.csv`.

## Iteration 0 → pipeline bug (before any scientific result)
- **Observation:** in the one-seed MPEA-hardness smoke test every CV+ variant covered ~0.45 even under random splits, which is impossible for correct CV+.
- **Cause:** `weighted_lower` evaluated the lower quantile at level α instead of 1 − α, which produced one-sided intervals.
- **Fix and verification:** corrected. The output now equals the direct CV+ order-statistic formula exactly, and this is covered by the unit test `test_weighted_quantiles_match_cvplus_order_statistics`.
- **Status:** bug fix, not a method change. No result produced before the fix is used anywhere.

## Iteration 1 → v2 scale model (input clamping)
- **Observation:** interim analysis of the three alloy tasks, 90 runs, α = 0.1. Under the cluster protocol FCP v1 reached mean coverage 0.919, but its **mean** interval width was 6.64 SD(y), against median widths of about 2–3 SD(y). Its mean interval score was 7.36, worse than every baseline.
- **Diagnosis:**
  - The width distribution was extremely heavy-tailed. On MPEA yield strength, cluster protocol, seed 0: median 2.19 SD, mean 6.73 SD, maximum 1,563 SD.
  - The affected test alloys had compositional novelty d(x) well outside the range of family-out-of-bag novelty used to fit the log-linear scale model; rare one-hot processing categories become large values after standardization. The model σ = exp(a + b log s + c log d) was therefore extrapolated far beyond its fitting range.
  - The same pathology appeared in the random-fold normalized baseline NCV+ (maximum 454 SD), so it is a property of the scale model, not of grouping.
- **Hypothesis:** clamping log s and log d to the [min, max] range seen when fitting the scale model removes the unbounded widths while leaving coverage essentially unchanged.
- **Implementation:** `ScaleModel(clip=True)`, set in config as `clip_scale: true`. It applies to every normalized variant (FCP, FCP-W, GCV+[spread/novelty], NCV+), baselines included, so the comparison stays fair.
- **Pre-check (one run, MPEA yield strength, cluster, seed 0):** FCP v2 coverage 0.933; width median 2.19 / mean 2.43 / maximum 8.0 SD (v1 maximum 1,563). NCV+ v2 maximum 9.2 SD (v1 454).
- **Experiment:** all ten CV+ variants were re-run with v2 for all 6 tasks × 3 protocols × 10 seeds (experiment key `main`, variant `cvplus_v2`). All later experiments (robustness, generalization, sensitivity, efficiency) use v2.
- **Comparison:** the v1 vs v2 table is generated automatically (`tables/table_iteration_v1_v2.csv`) for the runs where v1 exists: the three alloy tasks.
- **What was not changed:** folds, seeds, base learner, hyper-parameters, the definition of novelty, and the baselines' own settings.

## Iteration 2 → RF tree-spread normalization (Reviewer #8 hypothesis; recorded before the full run)
- **Observation:** with random-forest ensemble members (stage `basemodel`), FCP's coverage matched LightGBM-based FCP: 0.918 / 0.892 vs 0.923 / 0.899. RF-z, a single 300-tree forest giving μ ± z·(tree SD), kept a significantly better interval score than FCP[RF] (12/12 cells, p = 0.0005), while covering 0.950 / 0.914 without any calibration.
- **Hypothesis:** RF-z's efficiency comes from the per-tree spread, a more informative heteroscedastic signal than FCP's member-level spread. Family-grouped CV+ normalized directly by tree spread (σ = s_tree + β, β = 0.1·median s over the calibration fold) should therefore combine family-level calibration with RF-z's efficiency.
- **Implementation:** `CrossFitRFSigma` (`models/conformal.py`) and stage `rfsigma`: methods FCP-RFsigma (grouped folds), CV+-RFsigma (random folds) and RF-z. All 6 tasks × 3 protocols × seeds 0–4.
- **Pre-check (one run: MPEA hardness, cluster protocol, seed 0):**

  | Method | Coverage | Interval score |
  |---|---|---|
  | FCP-RFsigma | 0.868 | 3.14 |
  | CV+-RFsigma | 0.837 | 2.96 |
  | RF-z | 0.950 | 2.95 |

  The hypothesis is not supported on this run. The full run decides; whatever the outcome, it is reported in Section 9.5.
