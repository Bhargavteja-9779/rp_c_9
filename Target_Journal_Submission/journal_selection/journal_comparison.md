# Journal Comparison (Phase 0)

Constraint set given by the user: JCR Q1, high JIF, reputable publisher (OUP-like quality, **not MDPI**), and **final acceptance ≤ 72 days**.

## Method for acceptance-time verification
Three independent sources were used. They are kept strictly separate from "first decision" figures:
1. **Crossref per-article history (own computation).** `scripts/crossref_acceptance_times.py` reads the `received`/`accepted` assertions that Springer Nature, Wiley, T&F and IET deposit. It reports the median and IQR of (accepted − received) for articles published since 2025-05. Output: `crossref_acceptance_times.csv`, `crossref_acceptance_times_2.csv`.
2. **PubMed article history (own computation).** `scripts/pubmed_acceptance_times.py` reads PubMed `<History>` received/accepted dates (published 2025-06 to 2026-11). Output: `pubmed_acceptance_times.csv`. It covers OUP and Elsevier journals indexed in PubMed. IEEE records carry no received dates.
3. **Publisher-reported averages.** Elsevier "Journal Insights" and OUP "About" pages. Elsevier figures come from search-engine snapshots because ScienceDirect blocks automated fetching. OUP pages were read directly.

Caveat for (1) and (2): only *accepted and published* papers are visible. Recent windows are biased toward fast papers (right-censoring). For JKSU-CIS, for example, the 74-day all-sample median rises to 82–93 days for 2025 receipt cohorts.

## Candidates evaluated (≥10 required; 60+ measured)

| # | Journal | Publisher | JIF (source) | Q1? | Median received→accepted (own) | Publisher-reported | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Bioinformatics | OUP | 5.5 (OUP page, 2025) | Q1 | **139 d** (PubMed, n=561) | 23 d to *first* decision (not acceptance) | Rejected: acceptance >72 d; topic would need to be bioinformatics |
| 2 | Briefings in Bioinformatics | OUP | 7.3 (OUP page) | Q1 | **127 d** (n=595) | 8 d to first decision | Rejected: >72 d |
| 3 | JAMIA | OUP | 7.1 (OUP page) | Q1 | **122 d** (n=357) | n/a | Rejected: >72 d |
| 4 | GigaScience | OUP | — | Q1 | **196 d** (n=110) | — | Rejected |
| 5 | J. Computational Design & Engineering | OUP | 6.8 (OUP page) | Q1 | not deposited | **15 weeks** to acceptance (OUP page) | Rejected: ~105 d |
| 6 | Journal of Big Data | Springer | — | Q1 | **224 d** (Crossref, n=403) | 193 d median (2024, Springer) | Rejected |
| 7 | Complex & Intelligent Systems | Springer | — | Q1 | **147 d** (n=644) | — | Rejected |
| 8 | Artificial Intelligence Review | Springer | — | Q1 | **194 d** (n=372) | — | Rejected |
| 9 | Scientific Reports | Nature | — | Q1 | **143 d** (n=981) | — | Rejected |
| 10 | npj Digital Medicine | Nature | — | Q1 | **145 d** (n=988) | — | Rejected |
| 11 | J. King Saud Univ. – CIS | Springer (2025–) | 6.4–8.8 (conflicting aggregators) | Q1 | **74 d** overall; **82–93 d** for 2025 receipt cohorts | — | Rejected: just above the limit after censoring correction |
| 12 | Journal of Cheminformatics | Springer/BMC | 5.7 (2024) | Q1 | **137 d** (n=303) | 131 d (BMC page) | Rejected |
| 13 | Neural Computing & Applications | Springer | — | Q1/Q2 | **264 d** | — | Rejected |
| 14 | Energy Informatics | Springer | 5.5 (aggregator) | **SJR Q2; no JCR Q1 evidence** | 69 d (n=177) | — | Rejected: Q1 not supported |
| 15 | Computational & Structural Biotechnology J. | Elsevier | — | Q1/Q2 | **92 d** (PubMed) | — | Rejected |
| 16 | Computers in Biology & Medicine | Elsevier | — | Q1 | **141 d** | — | Rejected |
| 17 | Neural Networks | Elsevier | — | Q1 | **219 d** | — | Rejected |
| 18 | Medical Image Analysis | Elsevier | — | Q1 | **240 d** | — | Rejected |
| 19 | Results in Engineering | Elsevier | 7.9 (aggregator) | Q1 | not deposited | **74 d** (Insights), 76 d (other snapshot) | Rejected: just above 72 d; broad engineering scope |
| 20 | Alexandria Engineering Journal | Elsevier | 6.8 (aggregator) | Q1 | not deposited | **118 d** | Rejected |
| 21 | Eng. Sci. & Technol., Int. J. (JESTECH) | Elsevier | 5.4 (aggregator) | Q1 | not deposited | **139 d** | Rejected |
| 22 | Ain Shams Engineering Journal | Elsevier | — | Q1 | — | **149 d** | Rejected |
| 23 | Egyptian Informatics Journal | Elsevier | 4.3 (aggregator) | — | — | **183 d** | Rejected |
| 24 | Energy and AI | Elsevier | 9.6 (Insights) | Q1 | — | **95 d** | Rejected |
| 25 | Journal of Energy Storage | Elsevier | — | Q1 | — | **107–117 d** | Rejected |
| 26 | Computers & Electronics in Agriculture | Elsevier | — | Q1 | — | **172–188 d** | Rejected |
| 27 | Case Studies in Thermal Engineering | Elsevier | — | Q1 | — | **96–104 d** | Rejected |
| 28 | Developments in the Built Environment | Elsevier | — | Q1 | — | **89 d** | Rejected |
| 29 | Smart Agricultural Technology | Elsevier | 5.7–7.1 (conflicting) | listed **ESCI**; quartile unclear | — | **67–72 d** | Runner-up: meets timeline, but ESCI indexing and conflicting JIF are risks |
| 30 | **Journal of Materials Research and Technology** | Elsevier | **≈7.3** (aggregator, JCR 2026 release) | **Q1 (SCIE, 2 categories)** | not deposited | **67 d** to acceptance; 34 d to decision after review | **SELECTED** |
| 31 | IEEE TNSRE / JBHI / TMI / TNNLS | IEEE | — | Q1 | no received dates in PubMed or PMC | — | Unverifiable; rejected on verification grounds |
| 32 | Int. J. Intelligent Systems; Expert Systems; CAAI TIT; IET Image Proc. | Wiley/IET | — | various | 146–176 d | — | Rejected |
| 33 | Connection Sci.; Applied AI; JETAI; Int J Prod Res | T&F | — | various | 173–418 d | — | Rejected |
| 34 | J Neural Eng; Physiol Meas | IOP | — | Q1/Q2 | 128–141 d | — | Rejected |
| ref | Biosensors (MDPI) | MDPI | — | — | 39 d | — | Excluded by user instruction (reference only) |

## Decision logic
- Among OUP, Springer Nature, Wiley, T&F, IOP and IEEE titles in computing, informatics and AI, none had a measured or publisher-reported median acceptance ≤72 days.
- Elsevier publishes "submission to acceptance" averages per journal. Only Journal of Materials Research and Technology (67 d, SCIE Q1, JIF ≈7.3) and Smart Agricultural Technology (67–72 d, ESCI) meet the timeline.
- JMR&T was chosen over Smart Agricultural Technology for SCIE indexing, a consistent Q1 status in two categories, a higher and less ambiguous JIF, and a large, active ML-for-alloys readership.
- **Consequence for research design:** the topic must be genuine materials (metallurgy) research. Hence the selected topic is reliability of ML-predicted alloy properties under alloy-family extrapolation.
