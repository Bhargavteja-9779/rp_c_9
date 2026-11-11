# Review Round 2: Reviewer #2 (novelty, prior art, contribution differentiation)

**Focus:** whether the contribution is incremental, whether the gap is real, and whether prior art already solves the problem. Reviewer #1's points are not repeated.

## Prior-art search performed for this review
- Cheminformatics recalibration under drift. Found and verified via Crossref:
  - Morger et al., *J. Cheminform.* 13 (2021) 35, doi:10.1186/s13321-021-00511-5.
  - Morger et al., *Sci. Rep.* 12 (2022), doi:10.1038/s41598-022-09309-3.
  - Both show that conformal validity is lost under temporal or external drift and is **restored by swapping in a calibration set from the new domain**.
- Group or cluster conformal prediction. Group-conditional and Mondrian calibration are established (Vovk et al. 2005; group-partitioning work, CVPR-W 2025; Bhattacharyya & Barber 2026). Hierarchical prediction for new groups is covered by Dunn et al. (2023). No work was found that combines family-grouped CV+, a leakage-free normalized scale and a multi-dataset alloy benchmark.
- Materials conformal prediction:
  - Boruah 2026: steel fatigue, random splits.
  - Akdoğan 2026; Han et al. 2026: polymers, diagnostics only.
  - No alloy-family holdout study found (searches: "conformal prediction alloy unseen chemical system", "leave-one-cluster-out conformal materials").

## Issues

| # | Severity | Issue | Required fix |
|---|---|---|---|
| 2.1 | **MAJOR** | **Missing closest prior art.** Morger et al. already showed that matching the calibration set to the deployment domain restores coverage. Without this citation the paper overstates its conceptual novelty. | Cite both papers. Differentiate precisely: their remedy needs labelled data from the shifted domain, while FCP simulates the shift inside the training data before any new-family alloy is measured. |
| 2.2 | **MAJOR** | **Combination-of-known-parts critique.** Grouped CV (LOCO-CV), CV+, normalized scores and hierarchical exchangeability all exist. The introduction implies more originality than the method has. | State explicitly which ingredients are known and what is added: the combination for the alloy-family shift, the explicit estimands and finite-sample condition, the leakage-free scale, and the multi-dataset evidence. |
| 2.3 | **MAJOR** | **Is the criticized practice a straw man?** Few materials papers use random-split conformal prediction. Most use GP or ensemble σ, sometimes recalibrated on random held-out data (Palmer et al. 2022). | Show that the argument covers that practice too. GP and Ens-z are already baselines. Make explicit that NCV+ (σ-normalized, random folds) is the conformal analogue of recalibrating ensemble σ on random held-out data. |
| 2.4 | **MAJOR** | **Missing natural competitor: Mondrian (group-conditional) conformal prediction on novelty bins.** If coverage fails mainly for novel alloys, calibrating separately per novelty level might suffice without grouping. | Add MCP: split conformal with separate quantiles per tertile of compositional novelty, random calibration split. Run it on all tasks, protocols and seeds, and report it. |
| 2.5 | MODERATE | **Title overclaims.** "Prediction intervals that remain valid for unseen alloy families" asserts validity, but FCP's worst cell is 0.851 and no finite-sample guarantee is proved. | Use a neutral title. |
| 2.6 | MODERATE | **Theoretical novelty.** The paper should not suggest that the family-weighted construction is new theory. It is Dunn et al.'s pooling applied within CV+. | Already stated in Section 4.4 ("We make no claim of a new finite-sample theorem…"). Keep. |
| 2.7 | MINOR | **"First" claims.** Checked: the manuscript makes no "first" claim. The related-work statement is hedged ("To our knowledge…"). | None. |

## Author response and changes (Round 2 revision)
- **2.1 Fixed.** Section 2.2 now discusses Morger et al. [2021, 2022] and draws the distinction above. The Discussion ("Relation to prior work") states that recalibration with new-domain labels works when such data exist, and that FCP is the corresponding remedy *before* any alloy of the new family has been measured. Both DOIs were added to `scripts/verify_references.py` and verified.
- **2.2 Fixed.** A new paragraph at the end of the Introduction's method overview says that none of the ingredients is new on its own, and names the four elements that are added.
- **2.3 Fixed.** Section 5.4 now introduces NCV+ as "the conformal analogue of recalibrating ensemble uncertainties on randomly held-out data [Palmer et al.] and of the normalized method of [Boruah]". The ablation already shows that NCV+ under-covers under family shift (0.884 / 0.857). The critique therefore applies to recalibrated model-based σ, not only to random-split conformal prediction.
- **2.4 Fixed by a new experiment.**
  - MCP is implemented in `src/fcp/evaluation/protocol.py`, as stage `mondrian`: 6 tasks × 3 protocols × 10 seeds.
  - Smoke test (steel, cluster protocol, seed 0): SCP 0.622 → MCP 0.712. This is a partial improvement, still far from nominal.
  - Full results are reported in Section 9 (analysis: `table_mondrian.csv`).
- **2.5 Fixed.** New title: "Prediction intervals for alloys from unseen families: family-calibrated conformal prediction for machine-learned alloy properties".
- **2.6 / 2.7** No change needed. Checked.

## Residual novelty risk after Round 2
Moderate. A reviewer may still call the method "LOCO-CV + CV+". The defence rests on four points:
1. The explicit estimand and the finite-sample analysis (Eq. 10).
2. The leakage-free FOOB scale model.
3. Evidence that the obvious alternatives fail under family shift: density-ratio weighting, Mondrian-by-novelty, recalibrated σ (NCV+) and group-split calibration (GSCP).
4. The decision-level consequence for alloy screening.
