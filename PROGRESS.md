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
- [x] Phase 9-10 implementation (tests pass)
- [~] Phase 11-19 experiments running (v2 scale model, see supplementary/iteration_log.md)
- [~] Phase 20-23 figures/tables/manuscript (draft built by manuscript/tools/build_manuscript.py + build_docx.js)
- [~] Phase 24-33 reviews: review_01 done
- [ ] Phase 34-42 audits, docx, cover letter, risk report

## Open issues found during analysis (to be handled in review rounds)
- Cluster protocol: greedy size-balanced assignment of 10 distinct-size clusters to 5 outer folds is deterministic,
  so the 10 seeds share the same outer partition (seed SD reflects only internal randomness). Plan: Reviewer-3 round ->
  extra experiment with fully random cluster-to-fold assignment (stage `randfolds`), report both.
- RF-z (uncalibrated RF tree spread) matches FCP coverage under shift with better interval score; it over-covers
  in-distribution (0.955 at nominal 0.90). Base-model swap experiment (stage `basemodel`, FCP with RF members) queued.
- Main results available: results/raw_results.csv, statistics.json, tables/, figures/ (analysis stage).
- Review rounds 1-4 written (REVIEW/). Metric fix (empty CQR intervals) requires recompiling CSVs from cache at the end:
  `cd Target_Journal_Submission/code && python3 run_all.py --mode full --stage main,robustness,generalization,sensitivity,basemodel,randfolds,mondrian,analysis`
  (all cached; efficiency excluded because it re-measures).
- Manuscript: `cd manuscript/tools && python3 build_manuscript.py && node build_docx.js spec.json ../Final_Manuscript.docx`
- Remaining: Sections 9 (robustness, generalization incl. basemodel/randfolds/mondrian, sensitivity) and 10 (efficiency) text;
  reviews 5-10; final audit; cover letter; risk report; final DOCX/PDF.
