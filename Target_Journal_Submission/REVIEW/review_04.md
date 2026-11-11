# Review Round 4 — Reviewer #4 (ML methodology, optimization, training protocol, implementation correctness)

**Method of review:** read the code in `code/src/fcp/` against Sections 4–5 of the manuscript, ran the unit tests, and audited all 360 cached main runs for completeness and validity. Issues from Reviewers #1–#3 are not repeated.

## Code ↔ manuscript contradictions and omissions

| # | Severity | Finding | Location | Fix |
|---|---|---|---|---|
| 4.1 | **MAJOR** | **Invalid intervals in a baseline.** In 4 of 360 runs (CQR, α = 0.2, cluster protocol, formation enthalpy and superconductors), some intervals had lower > upper. Separately trained quantile regressors can cross, and a negative conformal correction then inverts the interval. The metrics treated these as negative widths, which slightly *understated* CQR's mean width. | `models/conformal.py::cqr`; found by the cache audit | `evaluation/metrics.py`: an inverted interval is an empty set with width 0. It never covers, and its interval-score miss distance is measured to the nearer bound. `empty_rate` is now reported. New unit test `test_inverted_interval_counts_as_empty`. All result CSVs are recompiled from the cache with the corrected metric (stage list in `scripts/resume_all.sh` ends with `main,analysis`). Only secondary α = 0.2 CQR numbers can change. |
| 4.2 | MODERATE | The fallback threshold was "fewer than ten" in the text but `ok.sum() <= max(10, p + 2)` in the code. | `models/base.py::ScaleModel.fit` | Text changed to "ten or fewer". |
| 4.3 | MODERATE | **Undocumented scale floor.** σ is floored at the 5th percentile of its fitted values. | `ScaleModel.fit/predict` | Documented in Section 4.3. |
| 4.4 | MODERATE | **v2 clamping described only in the revision note.** The method section described the unclamped model. | Section 4.3 | The method now states that both signals are clamped to the fitting range at evaluation. |
| 4.5 | MODERATE | **Fit/apply mismatch of the spread signal.** The scale model is fitted on the FOOB spread, the SD over the 2–4 members that did not see the family. At evaluation it uses the SD over all *M* members, none of which saw the calibration fold. The two have different sampling variability. | `CrossFit.fit` | Validity is unaffected: calibration scores and test intervals use the same σ_k, so any monotone distortion is absorbed by the conformal quantile. The efficiency of the normalization could be sub-optimal. Disclosed in Section 4.3 ("the spread entering the fit is the FOOB spread"). Left unchanged so as not to modify the method after results. |
| 4.6 | MINOR | The few-families fallback in `FamilyBaggedLGBM` (row subsampling when there are fewer than 3 families) was undocumented. | `models/base.py` | Documented in Section 4.2. |
| 4.7 | MINOR | LightGBM `min_child_samples = 5` and `reg_lambda = 1` were not reported. | `config/default.yaml` | Added to Section 5.6. |
| 4.8 | MINOR | Table 2 called its model "the shared point predictor" without saying it is the ensemble fitted on the *whole* outer training part. CV+ intervals use the K fold ensembles instead. | `protocol.py::_fold_job` | Caption clarified. |

## Correctness checks that passed
- **CV+ quantiles:** the weighted quantile code reproduces the textbook CV+ order statistics exactly (unit test; numerical check against direct formula).
- **Leakage-free calibration:** for fold k, the ensemble, novelty scorer (scaler, PCA, kNN) and scale model are fitted on D₋ₖ only. Calibration labels of fold k enter only the scores (code inspection; `test_family_out_of_bag_only_uses_unseen_members`; `test_novelty_foob_excludes_own_family`).
- **Grouped folds never split a family** (unit test).
- **Completeness:** every outer test alloy has exactly one finite prediction and one interval per method, α and seed. There are no NaN bounds in the 360 cached runs, and lower ≤ upper everywhere except the CQR crossing above.
- **Determinism:** seeds are derived as seed·100 + fold; inner folds, bagging and LightGBM seeds follow from them.
- **Hardware:** CPU only; `run_info.json` records the device report.
- **Tests:** 12 unit tests pass (`python -m pytest tests -q`). New tests cover v2 clamping, unbalanced fold assignment and empty intervals.

## Residual methodological risks (disclosed in the manuscript)
- No hyper-parameter tuning, for FCP or any baseline. Section 13.
- The scale model is deliberately simple (log-linear, 3 parameters). Richer difficulty models could be more efficient but risk overfitting the FOOB residuals.
