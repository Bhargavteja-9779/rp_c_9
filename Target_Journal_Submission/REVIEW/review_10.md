# Review Round 10 — Final adversarial review (independent of Rounds 1–9)

**Instruction to myself:** try to reject the paper. Look for one fatal reason, then list every *genuine* major, moderate and minor weakness. Problems were not invented to reach a quota; where fewer real problems exist, fewer are listed.

## Search for a fatal flaw
Every candidate for a reason to reject outright was checked against data or code:

| Candidate fatal flaw | Check performed | Result |
|---|---|---|
| Calibration labels leak into the scale model or scores | Code inspection; unit tests on FOOB and fold separation (Round 4) | Not present |
| Test alloys of a held-out family appear in training | Grouped folds never split a family (unit test). Families are defined from composition only. | Not present |
| Identical compounds under different spellings cross folds | New audit (`scripts/audit_duplicate_spellings.py`): 199 SuperCon rows (96 compositions); none in other tasks. They cannot cross folds in the family protocols. In the random protocol, excluding them changes coverage by ≤ 0.004. | Real but negligible; disclosed in Limitations |
| Headline numbers not reproducible or typed by hand | All numbers are generated from `results/`; 75+ claims are checked at build time; the build fails if any claim breaks | Not present |
| Improvement is an artefact of seed selection or post hoc method changes | Seeds fixed in config; v1 kept and reported; FCP-RFσ labelled post hoc with its hypothesis logged before the run | Not present |
| Coverage gain is simply wider intervals | The interval score accounts for width. The ablation attributes the gain to grouping, not width. | Not present |

**No fatal flaw was found.**

## Major weaknesses (remaining after all revisions)
1. **No prospective or experimental validation.** All evidence comes from retrospective splits of public data.
2. **The best-performing variant (FCP-RFσ) is post hoc.** The confirmatory claims concern FCP; FCP-RFσ requires independent confirmation.
3. **External validity is bounded.** In the chronological hardness test every method failed (FCP 0.61), because of a within-family processing or measurement shift. FCP addresses family novelty only.
4. **The efficiency advantage is not robust at the dataset level** against CV+ (p = 0.094) and CQR (p = 0.062). Only six independent datasets were used.
5. **Family exchangeability is an assumption, not a verified property.** Adaptive design campaigns (feedback shift) violate it.
6. **A mis-specified family definition costs coverage** (0.814 when calibrating on systems for a cluster shift). The user must choose the family level.
7. **Under-coverage of extreme-property families persists** (FCP ≈ 0.82 in the most extreme sextile). These are the alloys a designer most wants.
8. **Composition-only features for steels** (no processing) and partly encoded processing for MPEAs. Large irreducible error inflates every interval.

## Moderate weaknesses
1. FCP is conservative in-distribution (0.941 at nominal 0.90) and wider than random-split methods (+23% width under the system protocol, +102% under the cluster protocol).
2. FCP-W is unusable with fewer than nine families (by construction). The cluster protocol has only ten families per dataset.
3. The cluster protocol's balanced fold assignment is deterministic across seeds. The randomized check shows no change in conclusions (0.904 vs 0.902), but the main tables use the deterministic version.
4. SuperCon was subsampled to about 4,000 compounds.
5. GP capped at 800 training alloys; CQR shares the point model's hyper-parameters. Both are documented, and both could be argued to handicap those baselines.
6. No hyper-parameter tuning for any method. The sensitivity study covers FCP only.
7. Family threshold (1 at.%) and cluster count (10) fixed and not varied.
8. Scale model fitted on FOOB spread but applied with all-member spread. Validity is unaffected; efficiency may be sub-optimal.
9. Interval scores are averaged across datasets after SD(y) normalization, which treats datasets as equally important.
10. Two of the twelve shift cells fall below 0.88 for FCP (cluster protocol: steels 0.877 and superconductors 0.851).
11. Paper length (31 pages, 12 figures, 9 tables) may prompt requests to shorten.

## Minor weaknesses
1. Memory measurements are dominated by the interpreter baseline.
2. Energy was not measured.
3. Repository DOI, authors, CRediT, funding and acknowledgements are placeholders (author action).
4. Two references are arXiv preprints (Boruah 2026; Tan et al. 2025). They are relevant, but not peer-reviewed.
5. The steel and superconductor tasks are not alloys in the metallurgical sense for all entries (SuperCon includes oxides). This is framed as external validity.
6. The PDF rendering of OMML equations depends on LibreOffice; Word renders them natively.

## Author actions taken in this round
- New audit script and limitation for duplicate spellings, with impact quantified and claim-checked.
- Limitations extended: no prospective validation; post hoc status of FCP-RFσ; fixed family threshold and cluster count.
- Every remaining weakness listed above is disclosed in the manuscript (Limitations, Sections 7.3, 9.2, 9.3, 9.5, 11). None is hidden.

## Verdict of the adversarial reviewer
The paper cannot be rejected on a fatal flaw. Its weaknesses are limitations of scope and of retrospective evidence, and they are declared openly. A fair outcome is **major or minor revision**, with likely requests for prospective validation and for shortening.
