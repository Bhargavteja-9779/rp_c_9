# Research design (Phases 2, 5, 6, 7, 8) — fixed before the full results were inspected

Git history records this file's commit before the main experiment campaign completed. A one-seed pipeline check on a single dataset, MPEA hardness, was run beforehand to debug the code. It found a lower-quantile bug (fixed) and the weighted-interval infinite-width limitation described below.

## Novelty map (Phase 4)
- Boruah 2026 → conformal intervals for steel fatigue under **random** splits; conditional coverage across label quartiles.
- Akdoğan 2026 / Han et al. 2026 → split-CP coverage **diagnosed** under chemistry holdouts (polymers); no remedy.
- MatUQ 2025 / Omee 2024 / Meredig 2018 → OOD *accuracy* and uncertainty–error correlation; no coverage guarantees.
- Dunn et al. 2023 / Bhattacharyya & Barber 2026 → statistical theory for group-level exchangeability and group-wise shift; no materials application, and no normalized CV+ with a novelty-aware scale.
- **This work → genuinely different elements:**
  - Calibration matched to the alloy-design deployment shift: CV+ folds grouped by alloy family.
  - A scale model fitted on **family-out-of-bag** residuals of a family-subsampled ensemble, so calibration labels never leak. Its inputs are ensemble disagreement and compositional novelty.
  - Explicit point-level (FCP) vs family-level (FCP-W) estimands, with the finite-sample requirement G ≥ ⌈(1−α)/α⌉ training families for FCP-W.
  - The first multi-dataset coverage benchmark for composition-based alloy models under family extrapolation.

What is **not** claimed as new: conformal prediction, CV+, normalized scores, grouped cross-validation, and LOCO evaluation are each established. The contribution is their principled combination for, and evaluation under, the alloy-family deployment shift. The empirical findings are also part of the contribution.

## Stress test (Phase 2), answered
- *Incremental?* Not if the paper shows that the dominant practice (random-split calibration, model-based σ) under-covers on unseen alloy families across datasets, and that family-level calibration fixes it at a quantified width cost. If grouping alone (GSCP or GCV+) does as well as FCP, that must be reported, and the contribution then rests on the benchmark and the calibration principle, not on the normalization.
- *Simpler method achieves it?* Simple group-split CP (GSCP) and RF-spread intervals are included as baselines for exactly this reason.
- *Dataset too small?* Six tasks with n = 312 to ~4,000 after deduplication and family-preserving subsampling.
- *Leakage?* See below.

## Hypothesis
Under alloy-family extrapolation, conformal intervals calibrated on randomly held-out alloys under-cover, because their calibration residuals measure interpolation rather than extrapolation error. Calibrating on residuals of whole held-out families restores near-nominal coverage on unseen families. Normalizing scores by ensemble disagreement and compositional novelty makes interval width adapt to the degree of extrapolation.

## Research questions → experiments
| RQ | Question | Experiment | Primary metric / test |
|---|---|---|---|
| RQ1 | Do random-calibrated conformal methods (SCP, CV+, CQR, WCP) and model-based intervals (GP, RF-z, Ens-z) keep 90% coverage on unseen chemical systems and composition clusters? | Exp 1 (main) | Cell coverage; H1 one-sided Wilcoxon vs 0.90 |
| RQ2 | Does FCP reduce the coverage shortfall relative to each baseline, and at what width / interval-score cost? | Exp 1–2 | H2: Wilcoxon on shortfall; H3: Wilcoxon on interval score; Holm |
| RQ3 | Which component matters: family-grouped calibration, normalization (spread, novelty), family weights? | Exp 3 (ablation, 10 CV+ variants) | Mean coverage, interval score, high-novelty coverage; H4 |
| RQ4 | Is FCP robust to label noise, reduced training data, α, and its own hyper-parameters? | Exp 4 (robustness), Exp 7 (sensitivity), α sweep | Coverage at 0.10/0.25 SD noise, 50% families; one-factor-at-a-time grid |
| RQ5 | Does FCP generalize across datasets and shift types, including a mis-specified family definition (calibrate on systems when the true shift is clusters)? | Exp 5 (generalization) + 6 datasets × 3 protocols | Coverage under mis-specification |
| — | Cost | Exp 6 (efficiency) | Wall time, peak RSS per outer fold |
| — | Where does it still fail? | Exp 8 (error analysis) | Per-family coverage vs novelty, target extremity, family size |

## Pre-specified analysis choices
- Primary level α = 0.10. Secondary levels: 0.05 and 0.20.
- Unit of analysis = (task × shift protocol) cell, averaged over 10 outer-split seeds (0–9). The seeds were fixed in advance and are never chosen after seeing results.
- Two estimands, defined before the full results:
  - FCP (unweighted) targets point-level coverage on unseen families.
  - FCP-W (1/n_g weights) targets family-level coverage, and needs at least ⌈(1−α)/α⌉ = 9 training families at α = 0.1. With fewer families its interval is infinite by construction. This is reported, never hidden.
- Hyper-parameters (LightGBM, M = 6, family fraction 0.7, K = 5, kNN k = 5, 16 PCs) are fixed defaults, not tuned on test folds. Their influence is examined only in Exp 7.

## Datasets (Phase 7)
| Task | Source | Licence / access | Rows after cleaning | Families (systems) |
|---|---|---|---|---|
| MPEA hardness (HV) | Borg et al. 2020, Sci. Data | public (GitHub, CitrineInformatics/MPEA_dataset) | 418 (formula × processing, median) | 134 |
| MPEA yield strength | same | same | 760 (formula × processing × test type × temperature) | 149 |
| Steel yield strength | Matbench `matbench_steels` | public via matminer | 312 | 49 (elements ≥ 1 at.%) |
| Bulk modulus | Mansouri Tehrani et al. 2018 (`brgoch_superhard_training`, suspect values removed) | public via matminer | 2,319 | 1,651 |
| Experimental formation enthalpy | Kingsbury et al. 2022 | public via matminer | 2,135 | 1,319 |
| Superconductor Tc | Hamidieh 2018 / SuperCon (UCI id 464) | CC BY 4.0 | 15,542 deduplicated; ~4,000 used (whole systems sampled, seed 0) | 3,171 total |

## Leakage audit (Phase 8)
- **Duplicates:** identical inputs (same formula and measurement conditions) are merged by median target before any split. SuperCon held 5,721 duplicate formulas.
- **Subject / source leakage:** the outer test folds hold out whole families (system / cluster protocols) or whole formulas (random protocol). The same alloy measured under different conditions therefore never sits on both sides.
- **Preprocessing leakage:** Magpie features are deterministic per composition and use no target. Scalers, PCA and kNN are fitted on training rows only (per fold, and per inner fold).
- **Calibration leakage:** the scale model for inner fold k is fitted only on D₋ₖ, using family-out-of-bag residuals. Calibration scores of fold k are therefore computed with a model and a scale that never saw those labels. WCP's density-ratio classifier uses unlabeled test features (transductive by design, as in Tibshirani et al. 2019).
- **Feature leakage:** the families are defined from composition, and composition fractions are also features. This is intended, not leakage: the family is a property of the input.
- **Remaining caveat:** MPEA rows from the same publication can share experimental bias across different systems. This cannot be controlled with the available metadata.
