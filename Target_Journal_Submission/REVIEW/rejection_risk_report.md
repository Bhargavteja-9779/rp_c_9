# Final Rejection-Risk Report (Phase 41) and Self-Decision (Phase 42)

Target journal: *Journal of Materials Research and Technology* (Elsevier). Risk is not zero, and acceptance is not guaranteed.

| # | Risk | Evidence | Severity | Mitigation | Fixed? |
|---|---|---|---|---|---|
| 1 | **Novelty**: "LOCO-CV + CV+ is incremental" | All ingredients are known; the paper says so explicitly (Introduction). New since Round 10: Proposition 1 (family-level finite-sample guarantee for FCP-S), metallurgical interpretation, pre-registered confirmation. | Moderate → low–moderate | Contribution framed as the combination for the alloy-family shift, plus explicit estimands and finite-sample condition (Eq. 10), a leakage-free scale, and evidence that each obvious alternative fails: WCP, MCP, NCV+, GSCP and CV+-RFσ (Sections 7–9). Closest prior art cited and differentiated (Morger et al.; Boruah; Han et al.; Dunn et al.). | Mitigated; residual |
| 2 | **Methodology**: finite-sample guarantee only for FCP-S | Proposition 1 + Supplementary Note S1; FCP-S evaluated (family coverage 0.922, all tasks above the 0.655–0.794 bound, no efficiency loss vs FCP-W, p = 0.63). | Low–moderate | FCP and FCP-W validated empirically on 11 tasks; scope of the proposition stated in Limitations. | Largely fixed |
| 3 | **Dataset**: public compilations, composition-only steels, SuperCon subsample, duplicate spellings in SuperCon | Limitations; duplicate audit shows ≤ 0.004 effect. | Moderate | Eleven tasks (six exploratory, five confirmatory, incl. an independent band-gap set); impacts quantified. | Mitigated |
| 4 | **Statistics**: few independent units | Task-level efficiency is not significant vs CV+ (p = 0.094) or CQR (p = 0.062). Pre-registered confirmation on 5 new tasks: C1–C3 met (p_Holm = 0.0078); C5 met narrowly (p = 0.049). | Moderate → low–moderate | Analyses reported at cell, protocol and task level; Holm correction; n_eff; bootstrap CIs; claims worded to the weakest supporting level. | Mitigated |
| 5 | **Reproducibility** | Fresh clone, tests, quick run and bit-exact reproduction of a published run (max difference 4.4e-16). | Low | One-command pipeline, resumable cache, pinned versions, data checksums. | Fixed. A repository DOI is still needed (author action). |
| 6 | **Baselines**: claims of weakened baselines | GP capped at 800; CQR shares hyper-parameters; no tuning. | Low–moderate | Deviations documented (Section 5.4). The strongest baseline (RF-z) gets its own section and a constructive follow-up. | Mitigated |
| 7 | **Generalization** | Mis-specified family definition (0.814); temporal hardness failure (all methods). | Moderate | Reported in Sections 9.2–9.3, Abstract and Conclusions as the boundary of the method, with a practical rule for choosing the family level. | Disclosed |
| 8 | **Writing**: length (31 pp., 9 figures, 8 tables) | Secondary checks condensed (Section 9.6); 4 figures moved to the Supplementary Material. | Low–moderate | Each section maps to a research question. | Mitigated |
| 9 | **Journal formatting** | Elsevier YPYW accepts any consistent format at first submission. Abstract 246 words, separate highlights file (5 × ≤ 85 characters), graphical abstract ≥ 1328 × 531 px, keywords, declarations, numbered references with DOIs, line and page numbers. | Low | Live Guide for Authors to be re-checked by the authors (ScienceDirect was not machine-readable from this environment). | Mostly fixed |
| 10 | **Citations** | 50 references; 47 DOIs verified (Crossref; arXiv DOIs via the arXiv API); remaining items are books/software without DOIs or verified separately. | Low | Preprints are cited only for what they report; peer-reviewed alternatives are cited alongside. | Fixed |
| 11 | **Journal scope**: "statistics paper in a materials journal" | Materials framing: MPEA/steel datasets, screening use case, Section 7.6 (VEC regime, phase, alloy class, δ) with primary HEA phase-rule literature; maraging steels, refractory MPEAs, processing shifts. | Moderate → low–moderate | The cover letter explains the fit; the inorganic tasks are positioned as external validity. | Mitigated; residual |
| 12 | **Journal-specific reviewer risk**: requests for experimental validation | No prospective synthesis possible with public data. | Moderate–high | Chronological test used as a proxy; limitation stated. | Not fixable within scope |
| 13 | **Publication integrity / compliance** | No fabricated data, results or citations. Generative-AI use declared. Post hoc analyses labelled. Negative results reported. Journal metrics flagged as secondary-source. | Low | Iteration log; claim audit; reproducibility audit. | Fixed. Author information and AI-use declaration to be confirmed by the authors. |
| 14 | **Post hoc best method** (FCP-RFσ) | Pre-registered confirmatory study (plan committed before any run): C4–C6 met, promoted by the fixed rule; qualifications (narrow C5, C6 on 3/5 tasks) reported. | Low–moderate | Section 9.5, Table 8, `supplementary/confirmatory_plan.md`. | Fixed |

## Journal-timeline caveat
JMR&T's 67-day "submission to acceptance" is a publisher-reported **average**, seen through a search-engine snapshot. Any revision round adds time, and this manuscript will probably receive at least one. Acceptance within 72 days is **not** assured. No Oxford, Springer, Wiley, Taylor & Francis or IOP computing journal with a verifiable median ≤ 72 days was found (`journal_selection/journal_comparison.md`).

## Round 11 ("max level") summary
See `review_11.md`. The confirmatory study, Proposition 1 with its empirical check (FCP-S), and the metallurgical section address the risks most likely to cause rejection. Two pipeline errors found during the upgrade were fixed and audited (missing Sections 9.4–9.6 in an intermediate build; quick-mode cache path). **Rejection remains possible.** The most likely outcomes are major or minor revision, and a desk rejection on scope cannot be excluded.

## Phase 42 self-decision

**READY FOR SUBMISSION** (scientifically and experimentally).

- All planned experiments have been run, and so have the eight additional experiments requested during the ten review rounds.
- Every claim is backed by machine-generated evidence, and the results reproduce bit for bit from a clean clone.
- No fatal flaw remains.

Remaining items are **administrative and can only be done by the authors**: author details and declarations, a repository DOI, and confirmation of JCR metrics and the live guidelines (`final_audit.md` §D). They do not require additional experiments.
