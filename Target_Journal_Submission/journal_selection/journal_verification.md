# Journal Verification Record

## Legitimacy and integrity checks for JMR&T
- Publisher: Elsevier, a long-established publisher. The journal is hosted on ScienceDirect and has a Crossref ISSN record (2238-7854) with DOIs under the prefix `10.1016/j.jmrt`.
- Not MDPI, not a hijacked title: DOIs resolve under Elsevier's prefix; Crossref lists thousands of 2024–2026 articles.
- No evidence was found of Clarivate "on hold" or delisting status in the sources consulted. Caveat: this was not checked against Clarivate's own list, which requires access.
- High publication volume (thousands of articles per year) is a mild quality-perception risk, not an integrity finding.

## What was verified first-hand vs. second-hand
| Item | First-hand (own query) | Second-hand |
|---|---|---|
| ISSN, publisher DOI prefix, article volume, ML-paper fit | Yes (Crossref API) | — |
| Submission→acceptance 67 d; →decision after review 34 d | No | ScienceDirect journal page snapshot (search engine) |
| JIF ≈7.3, Q1 | No | journalmetrics.org listing via search snippet; scijournal 7.85 |
| Abstract ≤250 words | No | Official Guide for Authors snippet |
| Highlights, graphical abstract, data statement | No | Third-party guide plus Elsevier general policy |

## Measurements that reject the other candidates (reproducible)
```
python3 scripts/crossref_acceptance_times.py crossref_acceptance_times.csv
python3 scripts/pubmed_acceptance_times.py pubmed_acceptance_times.csv
```
Both scripts use only public, documented APIs (Crossref REST, NCBI E-utilities). Results depend on the date they are run.

## Actions required by the authors before submission
1. Confirm the JIF and quartile in Clarivate JCR (institutional access).
2. Re-read the live JMR&T Guide for Authors for the highlights character limit, keyword count and graphical-abstract size.
3. Confirm the current APC and any waiver eligibility.
4. Remember that 67 days is a journal average and not a guarantee for this manuscript.
