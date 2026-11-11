# Review Round 1 — Reviewer #1 (general scientific review, hostile but fair)

**Manuscript:** "Prediction intervals that remain valid for unseen alloy families: family-calibrated conformal prediction for machine-learned alloy properties"
**Target journal:** Journal of Materials Research and Technology (JMR&T)
**Draft reviewed:** first complete draft. Sections 9 (robustness/generalization) and 10 (computational cost) were still awaiting experiments.

## Summary of the submission
The authors argue that conformal intervals for composition-based alloy property models are calibrated on random splits, and that this calibration fails when the test alloy belongs to an unseen family (chemical system or composition cluster). They propose FCP: family-grouped CV+ with a normalized scale model, fitted on family-out-of-bag residuals, plus a family-weighted variant. The paper benchmarks FCP against eight baselines on six public datasets.

## Issues

| # | Severity | Issue | Required fix |
|---|---|---|---|
| 1.1 | **MAJOR** | **Factual error in the abstract.** "In 360 evaluations (6 datasets, 3 split protocols, 10 seeds)": 6 × 3 × 10 = 180. The 360 figure counts cache files: CV+ variants were stored separately after the v2 revision. | Take the number from the data (`n_runs` = number of task × protocol × seed groups) and state the factorization. |
| 1.2 | **MAJOR** | **Weak materials relevance for JMR&T.** The paper reports coverage statistics but never shows a consequence for an alloy-design *decision*. A materials editor could desk-reject it as a statistics paper. | Add a decision-level experiment showing what calibration failure costs in alloy screening, together with metallurgical interpretation of the failures. |
| 1.3 | **MAJOR** | Figures 1 (workflow) and 2 (datasets) were generated but never placed, and figure numbers do not follow the order of first citation (Fig. 11 is cited before Figs. 5–10). | Place both figures; number figures and tables automatically in order of first citation. |
| 1.4 | **MAJOR** | The RF-z result weakens the headline. An uncalibrated random-forest heuristic matches FCP's coverage and has a numerically lower interval score. The paper must not imply FCP dominates. | Keep and expand the dedicated subsection (7.4), and test the constructive alternative (FCP with forest members). *Deferred to the base-model experiment; see Reviewer #8.* |
| 1.5 | MODERATE | Table 4: the FCP vs RF-z shortfall row shows Δ = 0 with CI [0, 0] and r = +0.67, which is confusing without explanation. | Explain in the caption that both shortfalls are zero in most cells. |
| 1.6 | MODERATE | Highlight 1 said "cover only 72–87% of unseen alloy families". Coverage is per alloy, not per family, and the upper end was taken from CV+ while the abstract used WCP. | Reword as "of new-family alloys" and use the same method range as the abstract. |
| 1.7 | MODERATE | FCP over-covers in the random protocol (0.941) and is wider than the random-calibrated methods. The text must state the width cost explicitly, not only through the interval score. | Already stated in 7.3 (width 1.47 vs 1.20 SD for the system protocol, 2.64 vs 1.31 for the cluster protocol); confirm it stays. |
| 1.8 | MODERATE | Sections 9 and 10 are cited but not yet written. | Write them when Experiments 4–7 finish (tracked). |
| 1.9 | MINOR | Equations: LibreOffice renders `|` and lone "+" superscripts in OMML incorrectly, and the nested subscript n_{g_i} was lost. | Use OMML delimiter objects for absolute values, the lo/hi notation for quantiles, and a flat n_{g(i)}. |
| 1.10 | MINOR | Table 1 used scientific notation for ranges (1.42e+03). | Use plain-number formatting. |
| 1.11 | MINOR | Citation numbering started in Section 5: table captions were resolved before the Introduction. | Resolve table citations when the table is placed. |

**FATAL issues:** none found. The research question is real, the evidence is from executed experiments, and the claims are checked against the results at build time.

## Author response and changes (Round 1 revision)
- **1.1 Fixed.** The abstract now reads "In 180 evaluation runs (6 datasets × 3 split protocols × 10 seeds)". The number comes from `V['n_runs']`.
- **1.2 Fixed.** New Section 7.5 and Table 5, "Consequences for alloy screening", computed by `screening_analysis()` in `code/experiments/analysis.py` from the cached per-alloy intervals.
  - Rule: an alloy is selected as a high performer if its lower bound exceeds the upper quartile of the property.
  - Pooled false-discovery proportion: SCP 4.6%, CV+ 3.4%, FCP 1.2%. Recall is lower for FCP (0.28 vs 0.38).
  - For MPEA yield strength the false-discovery proportion falls from 18% (SCP) to 7% (FCP).
  - Metallurgical interpretation of the worst families (maraging-type steels, refractory MPEAs, iron-pnictide superconductors) is in Section 11.
- **1.3 Fixed.** Fig. 1 is placed in Section 4.5 and Fig. 2 in Section 5.1. A two-pass numbering step (`number_refs`) assigns figure and table numbers by first appearance.
- **1.4 Partly addressed now, completed later.** Section 7.4 reports RF-z's systematic in-distribution over-coverage (0.955 at nominal 0.90; 0.911 at nominal 0.80). The base-model experiment (FCP with random-forest members, stage `basemodel`) is running; see Reviewer #8.
- **1.5 Fixed.** Caption extended.
- **1.6 Fixed.** The highlight now reads "Random-split 90% conformal intervals cover only 72–87% of new-family alloys". It is generated from the same quantities as the abstract and checked to be ≤ 85 characters.
- **1.7 Verified.** Present in Section 7.3; protected by the automated claim checks.
- **1.8 Open.** Experiments still running; tracked in PROGRESS.md.
- **1.9–1.11 Fixed.** Re-rendered and visually checked (LibreOffice PDF export).

## Automated claim audit after Round 1
`manuscript/claim_audit.json`: 40 directional claims are checked against the result files at build time. The build fails if any claim is not supported.
