# Review Round 6 — Reviewer #6 (computational complexity, latency, memory, energy, scalability, deployment)

**Question posed:** is the improvement worth its computational cost? Issues from Reviewers #1–#5 are not repeated.

## Evidence examined
- Per-fold wall time for every method and task, from the main runs. Each run was single-threaded, with 4 runs executing concurrently.
- Isolated-process measurements of wall time and peak RSS (MPEA yield strength and bulk modulus, unseen-system protocol, one fold): `efficiency_results.csv`.
  - FCP: 6.8 s and 14.3 s.
  - CV+: 7.1 s and 15.0 s.
  - SCP: 2.0 s and 3.6 s.
  - GSCP: 1.8 s and 4.1 s.
  - GP: 17.8 s and 21.5 s.
  - RF-z: 2.9 s and 9.9 s.
  - Peak RSS was about 345 MB for all methods (dominated by the Python and library baseline), except the GP at 445 MB.
- Sensitivity to *K* and *M* (Section 9.4). Cost scales linearly with *K*·*M*. *K* = 10 and *M* = 12 gave slightly sharper intervals.

## Issues

| # | Severity | Issue | Fix |
|---|---|---|---|
| 6.1 | **MAJOR** | **Cost–benefit is not argued.** FCP costs 3.5–6× split conformal prediction. The cheaper GSCP (family-held-out split) reaches 0.894 under the system protocol. The paper must say when the extra cost is justified. | New Discussion paragraph "Is the extra cost worth it?", computed from data. GSCP is close to FCP when many families exist (system 0.894 vs 0.922) but fails with few families (cluster 0.816 vs 0.902). FCP's benefit grows as the number of families shrinks, which is the realistic situation for a new alloy class. The recommendation now names GSCP as the cheaper option for databases with many families. |
| 6.2 | MODERATE | **Memory measurement is uninformative** about the method itself, because the interpreter baseline dominates it. | The text reports the measured peak RSS and does not claim memory advantages beyond the GP comparison. |
| 6.3 | MODERATE | **Scalability of interval formation.** CV+ needs O(*n* log *n*) work per test alloy. This is fine at 3,200 training alloys but could be prohibitive at 10⁵. | Added to Limitations, with the practical approximation (pooled quantile of normalized scores). |
| 6.4 | MINOR | **Energy not measured.** | Stated in Limitations. CPU-only runs; costs are given in wall time. |
| 6.5 | MINOR | Timing in Table "cost" was measured with concurrent processes. | The caption states it; isolated-process timings are reported separately (Fig. "efficiency"). |
| 6.6 | MINOR | The latency for a *new* alloy is not reported. | Once the K fold models are trained, predicting a new alloy costs K·M tree-ensemble evaluations plus one weighted quantile, which is milliseconds. The text in Section 10 states that the extra cost is incurred per model update, not per prediction. |

## Verdict
The cost is moderate in absolute terms: seconds per fold on one CPU thread, no GPU. It is small relative to the cost of a single alloy synthesis and test. The paper now gives a data-based rule for when the cheaper GSCP suffices. **No fatal or unresolved major issue remains in this domain.**
