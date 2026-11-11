# Review Round 7: Reviewer #7 (scientific writing, logic, unsupported claims, terminology, guideline compliance)

**Method:** read the complete rebuilt draft (about 10,500 words), checking it against the result files, internal consistency and the JMR&T / Elsevier author guidelines. Points from Reviewers #1–#6 are not repeated.

## Issues

| # | Severity | Issue | Fix |
|---|---|---|---|
| 7.1 | **MAJOR** | **Inconsistent numeric ranges across sections.** The Discussion gave random-calibrated coverage on unseen clusters as "72–75%" (SCP–CQR), while the Conclusions gave "0.72–0.86" (SCP–WCP). The highlight used yet another pair of methods. | One definition everywhere: the range over SCP, CV+, CQR and WCP (`rc_range()`), generated from data. The Discussion adds that the upper ends belong to WCP, which reached them only with infinite intervals. |
| 7.2 | **MAJOR** | **Logical error in Section 7.5.** "With family-level calibration, the stated confidence of a lower-bound screen holds…; with random-split calibration, it is overstated by a factor of three to four." Pooled SCP false discoveries (4.6%) are below the 5% implied by a 95% one-sided bound, so the "overstated" claim does not follow. The CV+/FCP ratio is 2.8, not 3–4. | Rewritten. All methods keep pooled FDP < 5%, but task-level differences are large: MPEA yield strength under SCP reaches 18%. Exact ratios are reported (SCP/FCP and CV+/FCP). New claim checks: ratios within 2.5–4.5, pooled FDP < 5%, MPEA-YS SCP FDP > 10%. |
| 7.3 | **MAJOR** | **Overclaim in the Discussion.** "That price was worth paying in every comparison except against RF-z" ignores the task-level results (not significant vs CV+, CQR). | Now: better than every baseline except RF-z at the 12-cell level; at the dataset level the advantage over CV+ and CQR is consistent in direction but not significant. |
| 7.4 | **MAJOR** | **Abstract and Conclusions omit the boundaries** found in Round 5: the mis-specified family definition and the temporal hardness failure. | Abstract: a data-conditional sentence on the chronological test (included only if `table_temporal.csv` supports it). Conclusions: new item 6 on what FCP certifies and what it does not. Item 2 now names the analysis level ("12 dataset-protocol cells, Holm-corrected") and the screening result. |
| 7.5 | MODERATE | **Introduction overclaim.** "…no calibration procedure … that remains valid…" implies that FCP is proven valid. | "…that restores coverage…". |
| 7.6 | MODERATE | **Contributions list incomplete.** The screening consequence and the chronological test are missing. | Contribution bullet added (Sections 7.5, 9.3). |
| 7.7 | MODERATE | **Elsevier compliance.** Highlights were printed inside the manuscript body (Elsevier requires a separate editable file), and there was no graphical abstract. | `manuscript/highlights.docx` and `highlights.txt` (5 bullets, each ≤ 85 characters, length-checked at build). `graphical_abstract.png` is 2456 × 944 px, above Elsevier's 1328 × 531 px minimum. It includes RF-z so that it does not cherry-pick baselines. |
| 7.8 | MINOR | **Terminology.** "Random-calibrated", "random-split calibration" and "calibrated on random splits" were used interchangeably. | Kept as synonyms, defined at first use in Section 5.4 ("Random-calibrated conformal baselines"). |
| 7.9 | MINOR | **Abstract length.** | 235 words (≤ 250), checked at build time. |
| 7.10 | MINOR | **Figure and table quality.** All figures are regenerated at 300 dpi with the validated palette. Legends do not overlap data (checked visually), and every table has its unit and averaging stated in the caption. | Done in Rounds 1 and 6. |
| 7.11 | MINOR | **Reference style.** Numbered, in order of first citation, with full author lists and DOIs from Crossref. Elsevier's "Your Paper Your Way" accepts any consistent style at first submission. | No change. |

## Mathematical consistency check
- The symbols μ_k, s_k, d_k, σ_k, S_i, Q^lo/Q^hi, w_i, w_∞ and G are used consistently in Eqs. (1)–(10) and the text.
- Eq. (5) and the code compute the same normalized absolute residual.
- Eq. (8) matches `weighted_upper` (unit test).
- Eq. (10) matches the observed infinite FCP-W intervals with 8 training clusters.

## Result
59 automated claim checks pass, with the abstract word count and highlight lengths included. The text, highlights, cover letter and conclusions now draw on the same data-generated quantities.
