# Selected Target Journal

**Date of selection:** 2026-11-10

| Field | Value | Source / verification status |
|---|---|---|
| TARGET JOURNAL | **Journal of Materials Research and Technology (JMR&T)** | — |
| PUBLISHER | Elsevier (on behalf of the Brazilian Metallurgical, Materials and Mining Association, ABM) | ScienceDirect journal page (via search-engine index; live page blocks automated access, HTTP 403) |
| ISSN | 2238-7854 (online) | Crossref journal record (queried directly, `api.crossref.org/journals/2238-7854`) |
| ACCESS MODEL | Gold open access | ScienceDirect |
| JCR STATUS | Indexed in Science Citation Index Expanded (SCIE) | Third-party JCR mirrors (journalmetrics.org listing); **not verified in Clarivate JCR directly** (no JCR subscription access in this environment) |
| JCR QUARTILE | Q1 (Materials Science, Multidisciplinary; Metallurgy & Metallurgical Engineering) | Third-party JCR mirror; not verified first-hand |
| JOURNAL IMPACT FACTOR | ≈7.3 (JCR 2026 release, 2025 data) per journalmetrics.org; 6.6 the previous year. Another aggregator reports 7.85. | **Conflicting third-party values; the exact JIF must be confirmed in Clarivate JCR before submission** |
| JCR SUBJECT CATEGORY | Materials Science, Multidisciplinary; Metallurgy & Metallurgical Engineering | Third-party JCR mirror |
| VERIFIED REVIEW/DECISION TIMELINE | Submission → decision after review: **34 days** (publisher-reported, ScienceDirect journal page snapshot) | Publisher figure seen through search-engine snapshot; live page not loadable |
| VERIFIED ACCEPTANCE TIMELINE | Submission → acceptance: **67 days** (publisher-reported average, ScienceDirect snapshot). Acceptance → online publication: 2 days | Publisher-reported, **not independently re-computed**: Elsevier does not deposit received/accepted dates in Crossref and JMR&T is not PubMed-indexed, so the per-article recomputation used for the other candidates was impossible for this journal |
| APC | USD ~1,800–1,930 (two ScienceDirect pages disagree) | Publisher pages via search snippets |
| SCOPE FIT | Metallurgy, materials science, materials processing and characterization; ML-assisted property prediction of alloys is published regularly (2,582 Crossref relevance hits for "machine learning prediction alloy" since 2024, incl. HEA hardness/yield-strength ML papers) | `jmrt_recent_ml_papers.txt` |
| RESEARCH FIT | Strong: the study addresses reliability of ML property predictions for alloy design, a direct concern of JMR&T's ML-for-alloys readership. No JMR&T paper on conformal / distribution-free uncertainty was found (Crossref query "conformal prediction" returned only unrelated "conformal polishing" papers). | `jmrt_recent_ml_papers.txt` |

## Key author guidelines (to be re-confirmed on the live Guide for Authors before submission)
- Abstract ≤ 250 words, standalone, no references (confirmed in official GfA snippet).
- Keywords section required (Elsevier standard: up to ~7 keywords).
- Highlights (3–5 bullets, ≤85 characters each, Elsevier standard) and graphical abstract — reported as required by a third-party guide; prepared in the package.
- Data availability statement, declaration of competing interests, CRediT author statement, declaration of generative-AI use in writing (Elsevier policy) — all included.
- Elsevier "Your Paper Your Way": any consistent reference style accepted at first submission; numbered references in square brackets are used.
- No hard word limit was found for full-length research articles.

## Key rejection risks
1. **Scope risk (moderate):** JMR&T is materials-centric. A purely statistical paper could be desk-rejected as "not materials research". Mitigation: alloy datasets only as primary evidence (HEA/MPEA hardness and yield strength, steels), metallurgically defined alloy families (chemical systems / base-element families), metallurgical interpretation of failures, and practical alloy-design guidance.
2. **Novelty risk (moderate):** conformal prediction is established; the contribution must be the family-level calibration under compositional extrapolation plus a rigorous multi-dataset benchmark, not "conformal applied to materials".
3. **No new experimental (lab) data:** mitigated by public, citable datasets and full reproducibility.

## Constraints that could not be fully satisfied/verified
- **No reputable non-MDPI Q1 journal with verified median acceptance ≤72 days exists among Oxford University Press, Springer Nature, Wiley, Taylor & Francis or IOP computing/ML/informatics titles** that were measured (see `journal_comparison.md`). All measured OUP journals had a median of 122–196 days from receipt to acceptance (PubMed history dates).
- JMR&T's 67-day figure is the **publisher's own reported average**, observed through a search-engine snapshot; it could not be independently recomputed. It is an average across accepted papers, not a guarantee for any individual manuscript. Revisions requested by reviewers can push any paper beyond 72 days.
- JIF and quartile come from third-party JCR mirrors; Clarivate JCR itself could not be accessed.
