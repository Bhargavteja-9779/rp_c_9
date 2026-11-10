# Autonomous research pipeline — progress log
Branch: claude/autonomous-research-discovery-795xcu. All deliverables are under Target_Journal_Submission/.

## Decisions (fixed)
- Target journal: Journal of Materials Research and Technology (Elsevier, SCIE Q1, JIF ~7.3, publisher-reported 67 d to acceptance). See journal_selection/.
- Topic: conformal prediction intervals for composition-based alloy property models that stay valid under ALLOY-FAMILY extrapolation.
  Proposed method: "Family-Calibrated Conformal Prediction (FCP)":
  normalized CV+ with family-grouped folds, family-balanced (1/n_g) weights and difficulty scale
  sigma(x) = exp(a + b log s(x) + c log d(x)), where s = spread of a family-subsampled bagged ensemble and d = kNN novelty distance.
  sigma is fit on family-out-of-bag residuals inside each fold's training data, so no leakage.
- Closest prior art: Boruah 2026 arXiv 2608.07589 (steel fatigue, random splits); Akdogan 2026 ACS Omega (polymer Tg, SCP only);
  Han et al. 2026 Polymers (SCP coverage 0.683 under class holdout, no remedy); MatUQ arXiv 2511.11697 (GNN OOD, no coverage);
  Dunn, Wasserman & Ramdas 2022 (hierarchical conformal); Barber et al. 2021 (CV+); Tibshirani et al. 2019 (weighted CP); Romano et al. 2019 (CQR).
- Datasets: MPEA (Borg et al. 2020) HV and YS; matbench_steels YS; SuperCon (UCI, Hamidieh 2018) Tc; Brgoch superhard bulk modulus; Kingsbury experimental formation enthalpy.
- Families: F1 = chemical system (element set); F2 = k-means clusters of composition.

## Phase status
- [x] Phase 0 journal selection (docs written)
- [x] Phase 1-4 topic + prior art (to be written into literature/ docs)
- [ ] Phase 9-10 implementation
- [ ] Phase 11-19 experiments
- [ ] Phase 20-23 figures/tables/manuscript
- [ ] Phase 24-33 reviews 01-10
- [ ] Phase 34-42 audits, docx, cover letter, risk report
