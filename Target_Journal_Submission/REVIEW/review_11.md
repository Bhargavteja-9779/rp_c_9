# Review Round 11 — "Max-level" upgrade: adversarial re-review after the confirmatory study

**Trigger.** The author asked for the paper to be raised to a level where outright rejection is unlikely ("at most major revision"). No outcome can be guaranteed. This round therefore targets the specific reasons a JMR&T editor or reviewer is most likely to reject: scope, the post hoc best method, few independent datasets, missing theory, and length. It also re-checks the whole pipeline for errors introduced during the upgrade.

## 1. Rejection reasons addressed in this round

| Rejection reason (Round 10 / risk report) | What was done | Evidence | Status |
|---|---|---|---|
| "Statistics paper in a materials journal" (scope) | Metallurgical analysis: coverage by VEC regime, phase constitution, alloy class and δ tertile. Primary HEA phase-rule literature cited and verified. | Section 7.6, Fig. 5, `table_metallurgy.csv`. Random-split failures concentrate in the VEC 6.87–8 band (yield strength: SCP 0.73, FCP 0.85) and in multiphase alloys. | Mitigated |
| Best-performing variant (FCP-RFσ) is post hoc | Pre-registered confirmatory study on five new tasks. The plan was committed (`3ec309e`, 12:03:31 UTC) before the first confirmatory run (first cached result 12:06:02 UTC). No re-runs, tuning or task substitutions. | Section 9.5, Table 8, `statistics_confirm.json`. C1–C6 all met, so FCP-RFσ is promoted under the pre-registered rule. | Fixed, with two qualifications stated in the text: C5 met narrowly (p = 0.049, 10 cells from 5 tasks); C6 holds on the mean but on only 3 of 5 tasks individually (FCP-RFσ over-covers steel tensile strength). |
| Only six independent datasets | Five further tasks. One (experimental band gap) is fully independent; four are new properties of partly the same materials (disclosed). | Section 9.5. FCP covered 0.919 / 0.909, SCP 0.846 / 0.782; C2 holds against SCP, CV+, CQR and GSCP (p_Holm = 0.0078 each). | Mitigated (11 tasks, 7 material sets) |
| No finite-sample theory | Proposition 1: family-subsampled FCP-S inherits Barber et al.'s K-fold CV+ bound at the family level. Full proof in Supplementary Note S1, including the equal-fold-size caveat. | Section 4.4 (Eq. 11) and Note S1. | Fixed for FCP-S; FCP and FCP-W remain empirical (stated in Limitations) |
| The theory concerns a variant that was never run | FCP-S implemented (`calibration_weights(..., "subsample")`, unit-tested) and evaluated (stage `fcps`, 6 tasks × 10 seeds, unseen-system protocol). | Section 9.6 (iv), Table S-fcps. Family-level coverage 0.922 (FCP-W 0.925); every task above its bound (0.655–0.794); interval score indistinguishable from FCP-W (p = 0.63). | Fixed |
| Length (31 pp., 12 figures, 9 tables) | Secondary checks condensed into Section 9.6. Sensitivity, α sweep, efficiency and parity figures moved to the Supplementary Material. | Now 9 figures and 8 tables; 31 pages including the confirmatory section and table. | Mitigated |

## 2. Errors found in this round and fixed
1. **Sections 9.4–9.6 were missing from the built manuscript.** During the restructure the hook that appends them to Section 9 was left returning an empty list. The base-learner/FCP-RFσ section and the condensed checks were therefore absent from the intermediate 28-page build, and their 14 claim checks were not executed. Restored; all 88 claims now pass.
2. **Quick-mode runs could write into the full-run cache.** `run_all.py` set the cache path only in the parent process, and joblib workers re-imported the default path. The cache directory is now passed through `FCP_RESULTS_DIR`.
   - Audit: all 1,338 full-run cache entries carry the full α grid, so none came from quick mode (which uses α = 0.1 only).
   - The six `fcps` quick pickles written to the full cache were deleted before the full `fcps` stage ran.
3. **Section 9.4 still called FCP-RFσ "to be confirmed"** after the confirmatory study. The text now points to Section 9.5, and the Conclusions state the outcome.
4. **Limitations still said that no finite-sample result exists.** They now state the scope of Proposition 1 (FCP-S only, conservative bound).
5. **Unexplained "∞" in the confirmatory table.** The caption now explains it (FCP-W under cluster holdout has G = 8 < 9; WCP density-ratio weights).
6. **arXiv references were listed as "NOT FOUND"** in `references_verified.csv`, because Crossref does not index arXiv DOIs. They are now verified against the arXiv API: 47/47 DOIs verified.
7. **Data source of the band-gap task was uncited.** Zhuo et al. (2018), DOI verified, is now cited, and every confirmatory task cites its data source.

## 3. Search for a fatal flaw (repeated)

| Candidate | Check | Result |
|---|---|---|
| Confirmatory study designed after seeing its results | Git timestamps of plan vs first cached run; single `stage confirm` in log | Not present |
| Confirmatory criteria re-interpreted to pass | C6 checked under both readings (|mean − nominal| and mean |cell − nominal|): both hold. C5 p = 0.0488 < 0.05 reported with three decimals and called narrow. | Not present; borderline result disclosed |
| FCP-S "guarantee" checked against the wrong quantity | Proposition 1 bounds coverage of a test alloy drawn uniformly from a new family, which is the family-coverage metric (mean of within-family coverage). The analysis uses `family_coverage`. | Correct |
| Upgrade-induced code changes alter published numbers | `calibration_weights` reproduces the old weights for True/False; 13 unit tests pass; the main-stage results are unchanged (cache reused, analysis re-run). | Not present |

**No fatal flaw was found.**

## 4. Remaining major weaknesses (cannot be removed within scope)
1. **No prospective synthesis.** All evidence is retrospective. The chronological tests (Sections 9.3 and 9.5) are the closest proxy.
2. **Confirmation is partly within-material.** Four of five confirmatory tasks share alloys or compounds with the exploratory tasks. Only the band-gap set is fully independent.
3. **FCP-RFσ's efficiency gain over FCP is modest and narrowly significant** on the confirmatory tasks (p = 0.049).
4. **The processing-shift failure** (chronological hardness, all methods ≈ 0.61) is outside what any family-level calibration can fix. It is reported as the boundary of the method.
5. **Family exchangeability is assumed.** Adaptive campaigns violate it.

## 5. Expected editorial outcome (honest estimate)
- The most likely outcomes are **major or minor revision**. The reviewer requests most likely to come up are experimental validation, more independent alloy datasets, and processing-aware features.
- A **desk rejection on scope** is possible if the handling editor sees it as a statistics paper. Section 7.6 and the cover letter address this, but cannot exclude it.
- **No outcome can be guaranteed.** Acceptance within 72 days is not assured either: the journal's 67-day figure is an average, and a revision round adds time.
