# Literature matrix and gap analysis (Phases 3–4)

Every entry below was verified against Crossref (`references_verified.csv`) or the arXiv API (`references_arxiv_verified.txt`). Content summaries for items 1–6 come from reading the papers' abstract and method sections during this study. The other items are characterised only at the level of their stated main contribution.

## A. Directly competing / closest work (uncertainty for materials property prediction under shift)

| # | Paper | Year | Venue | Problem | Data (size) | Split protocol | UQ methods | Key result | Limitation relative to this study | Code |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Boruah, "Distribution-Free Conformal Prediction for Steel Fatigue Strength: Marginal Validity Is Not Enough" | 2026 | arXiv 2608.07589 (preprint) | Interval prediction of steel fatigue strength | NIMS fatigue, n=437, composition + processing | **50 random splits** | SCP, cross-fitted normalized CP, Mondrian, CQR, GP, bootstrap, raw QR | SCP marginal 0.918 but 0.755 in highest-strength quartile; normalized CP restores 0.869–0.938 across quartiles | Only random splits: no compositional or family shift. One dataset. Conditioning is on the *label* quartile, not on alloy family or novelty | not stated |
| 2 | Akdoğan, "Trust Beyond Accuracy: Conformal UQ … Polymer Tg" | 2026 | ACS Omega 11(30) | Polymer Tg regression reliability | 410 MD-simulated polymers | stratified, scaffold, fingerprint-cluster CV | SCP only | Near-nominal marginal coverage; local under-coverage in low-similarity subsets | Diagnostic only. No method that restores coverage. Polymers, not alloys | — |
| 3 | Han et al., "What Random Splits Measure in Polymer Glass-Transition Prediction" | 2026 | Polymers 18(19) 2445 | Tg prediction under chemistry holdouts | 7,367 experimental Tg | random, scaffold, leave-class-out, high-Tg extrapolation | RF dispersion, RF split CP | RF split-CP coverage 0.899 (random), **0.683 (class holdout)**, 0.214 (property extrapolation); a similarity gate gives little protection | Shows the failure, proposes no conformal remedy. Polymers | Zenodo data |
| 4 | Tan et al., MatUQ | 2025 | arXiv 2511.11697 | OOD benchmark of crystal GNNs with UQ | 6 MatBench/JARVIS/SuperCon sets (636–106,113) | OFM-LOCO, SparseX/Y, SOAP-LOCO | MC dropout, deep evidential regression | Up to 70.6% MAE reduction; uncertainty–error Spearman ≤ 0.61 | No coverage guarantee and no conformal calibration. Structure-based GNNs, not composition-based alloy models | — |
| 5 | Varivoda et al., "Materials property prediction with UQ: a benchmark study" | 2023 | Appl. Phys. Rev. 10 | UQ for crystal GNNs | 4 crystal datasets | random (no distribution shift, per MatUQ) | ensembles, MC dropout, evidential, etc. | Ensembles not uniformly best | No distribution shift, no conformal coverage | — |
| 6 | Segal et al., "Known Unknowns: OOD property prediction in materials and molecules" | 2025 | npj Comput. Mater. 11 | Extrapolation to OOD **property values** | materials/molecules | property-range holdout | transductive extrapolation method | Improves OOD-value prediction | Target-range extrapolation, not interval coverage for unseen alloy families |
| 7 | Omee et al., "Structure-based OOD materials property prediction: a benchmark study" | 2024 | npj Comput. Mater. 10 | OOD benchmark | crystal structures | several OOD splits | — (accuracy) | GNN accuracy degrades OOD | No intervals |
| 8 | Meredig et al., "Can machine learning identify the next high-temperature superconductor?" | 2018 | Mol. Syst. Des. Eng. 3 | Extrapolation assessment | SuperCon | **leave-one-cluster-out CV (LOCO-CV)** | — | Random CV overstates discovery performance | Accuracy only, no UQ |
| 9 | Xiong et al., "k-fold forward cross-validation" | 2020 | Comput. Mater. Sci. 171 | Explorative prediction power | several | forward CV in target | — | Random CV overstates explorative power | No UQ |
| 10 | Tran et al., "Methods for comparing UQ for material property predictions" | 2020 | Mach. Learn.: Sci. Technol. 1 | UQ evaluation | adsorption energies | random | GP, ensembles, etc. | Calibration/sharpness metrics | No shift-aware coverage |
| 11 | Palmer et al., "Calibration after bootstrap" | 2022 | npj Comput. Mater. 8 | Recalibrating ensemble σ | several materials sets | random | bootstrap + recalibration | Bootstrap σ miscalibrated; recalibration fixes it | Recalibration on random held-out data, so the same exchangeability problem under family shift |
| 12 | Ling et al., FUELS | 2017 | IMMI 6 | Sequential design with calibrated RF uncertainty | materials sets | random | RF jackknife / infinitesimal jackknife | Calibrated uncertainties aid design | Not distribution-free; no family shift |

## B. Statistical foundations used by the proposed method

| # | Paper | Venue | Relevance |
|---|---|---|---|
| 13 | Vovk, Gammerman, Shafer (2005) *Algorithmic Learning in a Random World* | Springer | Conformal prediction |
| 14 | Lei et al. (2018) | JASA 113 | Split conformal regression; locally weighted (normalized) residuals |
| 15 | Papadopoulos, Vovk, Gammerman (2011) | JAIR 40 | Normalized nonconformity with kNN difficulty |
| 16 | Johansson et al. (2014) | Mach. Learn. 97 | Normalized CP with random forests |
| 17 | Vovk (2015) | Ann. Math. Artif. Intell. 74 | Cross-conformal predictors |
| 18 | Barber, Candès, Ramdas, Tibshirani (2021) | Ann. Stat. 49 | Jackknife+ / CV+ (the interval construction used here) |
| 19 | Romano, Patterson, Candès (2019) | NeurIPS (arXiv 1905.03222) | CQR baseline |
| 20 | Tibshirani, Barber, Candès, Ramdas (2019) | NeurIPS (arXiv 1904.06019) | Weighted CP under covariate shift (WCP baseline) |
| 21 | Dunn, Wasserman, Ramdas (2023) | JASA 118 | **Two-layer hierarchical exchangeability**: prediction for a new group. Motivates family-level calibration and the 1/n_g pooling |
| 22 | Barber et al. (2023) | Ann. Stat. 51 | Coverage loss bounds beyond exchangeability |
| 23 | Bhattacharyya & Barber (2026) | Electron. J. Stat. 20 | Group-weighted CP under group-wise covariate shift |
| 24 | Gibbs, Cherian, Candès (2025) | JRSS-B | Conditional guarantees |
| 25 | Fannjiang et al. (2022) | PNAS 119 | CP under feedback covariate shift (design loops) |
| 26 | Angelopoulos & Bates (2023) | Found. Trends ML 16 | Tutorial |
| 27 | Gneiting & Raftery (2007) | JASA 102 | Interval (Winkler) score |

## C. Materials ML context and data

Ward et al. 2016 (Magpie descriptors, npj Comput. Mater.); Ward et al. 2018 (matminer); Ong et al. 2013 (pymatgen); Borg et al. 2020 (MPEA dataset, Sci. Data); Hamidieh 2018 (superconductor data); Dunn et al. 2020 (Matbench); Mansouri Tehrani et al. 2018 (superhard training set, JACS); Kingsbury et al. 2022 (experimental formation enthalpies); Wen et al. 2019 and Rao et al. 2022 (ML-guided HEA design); Lookman et al. 2019 (active learning with uncertainty); Miracle & Senkov 2017 (HEA review); Breiman 2001 (RF); Hirschfeld et al. 2020 (UQ for molecular property NNs).

## Gap analysis

- **WHAT EXISTS?** (i) Evidence that random CV overstates accuracy for new chemistries (LOCO-CV: Meredig 2018; Xiong 2020; Omee 2024; MatUQ 2025). (ii) Conformal prediction applied to materials under *random* splits (Boruah 2026), plus diagnostics showing split-CP coverage collapses under chemistry holdouts in polymers (Akdoğan 2026; Han et al. 2026). (iii) Statistical theory for hierarchical, group-level exchangeability (Dunn et al. 2023) and group-weighted CP (Bhattacharyya & Barber 2026).
- **WHAT DOES IT FAIL TO ADDRESS?** No study (a) quantifies conformal coverage for **composition-based alloy property models** when the test alloy belongs to an **unseen alloy family** (new chemical system or composition cluster), or (b) provides and tests a **calibration procedure aligned with that deployment shift**. It is also unknown whether such a procedure (c) holds across alloy and inorganic datasets, and (d) what it costs in interval width relative to strong baselines: CQR, weighted CP, GP, RF-spread intervals, and simple family-held-out split calibration.
- **WHY DOES IT MATTER?** In alloy design the candidates of interest lie in chemical systems absent from training (e.g. new HEA systems). A nominal "90%" interval that covers only 64–85% there (Section 7 of the manuscript) gives false confidence when screening alloys or setting design margins.
- **WHAT WILL THIS RESEARCH ADD?** (1) A family-level calibration procedure (FCP / FCP-W): family-grouped normalized CV+, a scale model built from family-bagged ensemble disagreement and compositional novelty, and optional family-balanced weights. Its target estimands (point-level vs family-level coverage) and finite-sample limits are stated explicitly. (2) A multi-dataset benchmark (6 tasks, 3 split protocols, 10 seeds, 17 interval methods) of coverage under alloy-family extrapolation. (3) Ablations isolating grouping, normalization and weighting. (4) Robustness, sensitivity and error analyses identifying the alloy families on which intervals still fail.
- **HOW VERIFIED?** RQ1–RQ5 and Experiments 1–8 in `research_design.md`.
