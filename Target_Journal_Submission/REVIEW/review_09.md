# Review Round 9 — Associate Editor, *Journal of Materials Research and Technology*

**Role:** handling editor deciding whether to send the manuscript out for review, and anticipating the outcome. I evaluate the whole package (manuscript, supplementary material, code) rather than individual technical points.

## Assessment against the journal's criteria

| Criterion | Assessment | Risk |
|---|---|---|
| **Scope** | Reliability of ML property predictions for alloy design (MPEA/HEA hardness and yield strength, steels), with metallurgical interpretation of failures (maraging-type steels, refractory MPEAs, processing-route shifts) and a screening use case. Within JMR&T's materials-informatics stream, which regularly publishes ML-for-alloys papers. The three inorganic tasks are framed as external-validity checks, not as the paper's subject. | Moderate: a strongly metallurgical reviewer may find the statistics heavy. |
| **Novelty** | The individual ingredients are known, and the paper says so explicitly. The contribution is the family-level calibration for the alloy-design shift, the explicit estimands, and a broad, honest benchmark. That benchmark shows the obvious alternatives failing: density-ratio weighting, Mondrian-by-novelty, recalibrated σ, group-split calibration. It also identifies a calibrated variant that matches the strongest heuristic. | Moderate |
| **Technical quality** | Pre-registered design; leakage-free calibration; unit-tested code; 180 main runs plus about 600 additional runs across eight follow-up experiments. Statistics are reported at cell, protocol and task level, with Holm correction. A code ↔ manuscript audit was performed. | Low |
| **Evidence ↔ claims** | 75 distinct directional claims are checked automatically against the result files at build time. Negative results are reported in the main text: the temporal hardness failure, the mis-specified family definition, RF-z's efficiency, and the task-level non-significance against CV+ and CQR. | Low |
| **Completeness** | All experiment types required by the study design are present: main, baselines, ablation, robustness, generalization (mis-specification, temporal, base-learner), efficiency, sensitivity, error analysis, decision-level consequence. | Low |
| **Reproducibility** | One command reproduces every number; data are public; `scripts/resume_all.sh`; README with all stages. **Open item:** the repository DOI is a placeholder. | Moderate until deposited |
| **Clarity** | The paper is long: about 31 pages, 12 figures and 9 tables. Each section answers one research question, and Sections 9.6 and 9.7 are short. | Moderate: reviewers may request shortening |
| **Guidelines** | Abstract 246 words (≤ 250). Highlights in a separate file (5 bullets, ≤ 85 characters each). Graphical abstract 2456 × 944 px. Keywords (7). CRediT, competing-interest, data-availability and generative-AI declarations included. Numbered references with DOIs. Line numbers and page numbers present. | Low |

## Issues raised by the Associate Editor

| # | Severity | Issue | Action |
|---|---|---|---|
| 9.1 | MODERATE | Fig. 5 (empirical vs nominal coverage) was captioned but never cited in the text. | Fixed: cited in Section 7.4. An automated check confirms that every figure and table is cited. |
| 9.2 | MODERATE | **Two "best" methods.** The pre-specified FCP is the confirmatory method, yet the post hoc FCP-RFσ performs best. Readers must not confuse the confirmatory claims with the exploratory ones. | Already handled: Section 9.5, the Abstract ("a post hoc variant") and Conclusion item 4 label FCP-RFσ as post hoc; all hypothesis tests (H1–H3) concern the pre-specified FCP. |
| 9.3 | MODERATE | **Length.** | Kept. Every section maps to a research question or a reviewer-requested test, and the bulk tables are in the Supplementary Material. If the journal requests shortening, Sections 9.6–9.7 and Table 8 (computational cost) can move to the Supplementary Material without changing any conclusion. |
| 9.4 | MODERATE | **Repository DOI placeholder** in "Data and code availability". | **Author action required before submission:** deposit `code/` on Zenodo or a similar service and insert the DOI. Cannot be done without the authors' accounts. |
| 9.5 | MINOR | Author names, affiliations, CRediT roles, funding and acknowledgements are placeholders. | **Author action required.** |
| 9.6 | MINOR | The cover letter should not overstate scope fit, novelty or speed. | Checked: the letter states the contribution and its limits (RF-z competitor, hardest families) and makes no claim about review speed. |

## Would this manuscript survive peer review at JMR&T?
**Likely outcome: major or minor revision, not desk rejection**, provided the authors complete items 9.4–9.5.
- **Strengths a reviewer will credit:** a materials-relevant reliability problem, a careful design, multiple datasets, honest negative results, and full reproducibility.
- **Most probable reviewer requests:** shortening, more metallurgical interpretation of the failing families, and possibly a prospective or experimental validation. The last cannot be done with public data alone and is listed in the Limitations.
