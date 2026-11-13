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
- **Outcome (full run, 6 tasks × 3 protocols × seeds 0–4):** the hypothesis was **supported**.
  - Coverage of FCP-RFσ: 0.920 (system) and 0.912 (cluster).
  - Interval score: 1.85 / 2.81, against RF-z's 1.92 / 2.70. The paired 12-cell test finds no significant difference (p = 0.68); FCP-RFσ is better in 7 of 12 cells.
  - FCP-RFσ is better than LightGBM-based FCP in 11 of 12 cells (p = 0.0015).
  - Unlike RF-z it is calibrated in-distribution: 0.936 / 0.865 at nominal 0.90 / 0.80, against RF-z's 0.954 / 0.909.
  - The random-fold version (CV+-RFσ) under-covers (0.888 / 0.813), so grouping is still required.
  - The single-run pre-check was therefore not representative. This is reported as such and is a reminder why decisions were not taken on one seed.
  - Because the variant was formulated after the main results, the manuscript presents it as a post hoc finding (Section 9.5, Abstract, Conclusions). The pre-specified FCP remains the primary method of the confirmatory analysis.

## Iteration 3 — Pre-registered confirmatory study and FCP-S (Round 11)
- **Plan:** `confirmatory_plan.md`, committed in `3ec309e` (2026-11-13 12:03:31 UTC) before the first confirmatory run (first cached result 12:06:02 UTC). No setting was changed and no run was repeated afterwards.
- **Outcome (5 new tasks, 10 shift cells, 10 seeds):**
  - C1 met: SCP 0.846 / 0.782, CV+ 0.858 / 0.796, CQR 0.852 / 0.809 (system / cluster).
  - C2 met: p_Holm = 0.0078 against each of SCP, CV+, CQR and GSCP.
  - C3 met: FCP 0.919 / 0.909.
  - C4 met: FCP-RFσ 0.911 / 0.917.
  - C5 met narrowly: median paired interval-score difference −0.221 SD, p = 0.0488.
  - C6 met on the mean: |coverage − nominal| 0.035 vs 0.050 at α = 0.1 and 0.048 vs 0.100 at α = 0.2. Per task it holds on 3 of 5 tasks at each level; FCP-RFσ over-covers steel tensile strength.
- **Decision (fixed rule):** FCP-RFσ is promoted to the recommended variant for random-forest models, with the qualifications above stated in Section 9.5.
- **FCP-S (Proposition 1), added after Proposition 1 was written; not pre-registered:** 6 tasks × 10 seeds, unseen-system protocol.
  - Family-level coverage: 0.922 (FCP-W 0.925, FCP 0.912).
  - Every task is above its finite-sample bound (0.655–0.794).
  - Interval score vs FCP-W: p = 0.63.
- **Pipeline errors found and fixed:**
  1. Sections 9.4–9.6 were dropped from an intermediate build by an empty hook.
  2. Quick-mode joblib workers wrote to the full-run cache. Audit: no full-run entry was affected.
