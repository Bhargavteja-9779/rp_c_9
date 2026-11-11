# Review Round 3 — Reviewer #3 (statistical validity, fairness, seeds, splitting, leakage)

**Focus:** statistics and experimental fairness only. Issues raised by Reviewers #1–#2 are not repeated.

## Issues

| # | Severity | Issue | Evidence | Required fix |
|---|---|---|---|---|
| 3.1 | **MAJOR** | **Seeds do not re-randomize the outer partition in the cluster protocol.** The greedy, size-balanced assignment of 10 clusters of distinct size to 5 folds is deterministic, so all ten seeds share the same partition. Seed SDs under this protocol therefore reflect only model randomness. Visible symptom: the GP has SD = 0.000 on MPEA hardness/cluster. | `assign_folds(..., balanced=True)`; Table S2 | Re-run the cluster protocol with a fully random (unbalanced) cluster-to-fold assignment so that every seed uses a different partition. Report both. |
| 3.2 | **MAJOR** | **Non-independent units.** The 12 "cells" contain two protocols per task built from the same data. Treating them as 12 independent units inflates evidence. | Section 5.5 | Replicate the key tests at the task level (6 independent units; the two shift protocols averaged). Report the per-protocol tests (already present). |
| 3.3 | MODERATE | **Effective sample size of signed-rank tests.** Zero differences are dropped (`zero_method='wilcox'`). For FCP vs RF-z only 3 of 12 cells have a non-zero shortfall difference, so "not significant" says little. | `statistics.json` | Report n_eff in Table 4. |
| 3.4 | MODERATE | **Baseline fairness.** CQR reuses the point model's LightGBM hyper-parameters for quantile objectives. The GP is capped at 800 training alloys. WCP's density-ratio classifier is a design choice. These deviations can disadvantage baselines. | Section 5.4 | Document every deviation explicitly. Confirm that no method, proposed or baseline, was tuned on test folds. |
| 3.5 | MODERATE | **Data-dependent method revision.** The v2 scale clamp was introduced after an interim look at three tasks. This is a forking-paths risk. | `supplementary/iteration_log.md` | Report v1 results alongside v2. Apply the change to all normalized variants, baselines included. Show it does not alter coverage (only the tails of width). Already done in Section 8; keep. |
| 3.6 | MODERATE | **Leakage via family definition.** F2 clusters are computed by k-means on all alloys of a task, including outer test alloys. | `features.py` | This uses no labels and defines the deployment notion of "new". State it explicitly in the paper. |
| 3.7 | MINOR | **Multiple testing scope.** H4 (ablation) tests are uncorrected. | Section 8 | Label them exploratory. Already labelled in `statistics.json`. State it in the text. |
| 3.8 | MINOR | **Primary level.** α = 0.1 was pre-specified. Results at α = 0.05 and 0.2 are reported (Fig. 5). | — | None. |
| 3.9 | MINOR | **Seed choice.** Seeds 0–9 were fixed in the config before running, and no seed selection occurred. The configuration file and git history document this. | `config/default.yaml` | None. |

## Author response and changes (Round 3 revision)
- **3.1 Fix in progress (new experiment).** `assign_folds(balanced=False)` deals randomly permuted clusters round-robin to folds. Stage `randfolds` re-runs the cluster protocol for all 6 tasks × 10 seeds with SCP, CV+, CQR, WCP, RF-z, GSCP, GCV+, GCV+[spread], FCP and FCP-W. The analysis writes `table_randfolds.csv` comparing the balanced and random assignments. The limitation is stated in Section 13 and the comparison is reported in Section 9 once available. *(Result incorporated in Round 5; see review_05.md.)*
- **3.2 Fixed.**
  - Added `task_level_replication` to `statistics.json` and a paragraph in Section 7.3.
  - Shortfall: FCP is smaller than SCP, CV+, CQR, Ens-z and GSCP in **all six tasks** (exact p = 0.031, the minimum attainable with n = 6), and smaller than WCP and GP with p = 0.0625.
  - Interval score: consistent against SCP, GP, Ens-z and GSCP, but **not significant against CV+ (p = 0.094) and CQR (p = 0.0625)**. The text now states that the efficiency advantage over the best random-calibrated baselines is consistent in direction but limited by the number of datasets. This is a weaker claim than in Round 2.
- **3.3 Fixed.** Table 4 has an n_eff column, and the caption explains the ties.
- **3.4 Fixed.** Section 5.4 lists all deviations (CQR hyper-parameters, WCP classifier, GP cap, RF settings) and states that nothing was tuned on test folds.
- **3.5 Already handled.** Section 8 "Revision history"; Supplementary Table S1.
- **3.6 Fixed.** Section 5.5 now states that F2 families come from unsupervised clustering of all compositions, use no labels, and are fixed before splitting.
- **3.7 Fixed.** Section 8 refers to the H4 tests as exploratory (no multiplicity correction).

## Statistical summary after Round 3
- **Coverage (H1/H2):** the evidence is robust at the cell level, per protocol, and at the task level.
- **Efficiency (H3):** the cell-level evidence holds after Holm correction. At the task level it holds only against weaker baselines.
- **RF-z:** coverage cannot be distinguished from FCP. Its interval score is numerically better; the difference is not significant.
