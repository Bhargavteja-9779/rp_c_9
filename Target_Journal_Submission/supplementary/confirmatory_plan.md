# Pre-registered confirmatory study (written and committed BEFORE any confirmatory run)

**Purpose.** The exploratory study (6 tasks) produced two kinds of claims:
- *confirmatory* claims about the pre-specified FCP (H1–H3);
- one *post hoc* finding: FCP-RFσ, family-grouped CV+ normalized by random-forest tree spread.

This plan tests both on tasks that were **not used for any design, revision or analysis decision**. The git commit of this file precedes the first confirmatory run, which can be checked in the history.

## New tasks (fixed now)

| Key | Property | Source | Cleaning (same rules as before) |
|---|---|---|---|
| `mpea_uts` | Ultimate tensile strength (MPa) | MPEA database (Borg et al. 2020) | rows with UTS, test type C/T and test temperature; merged by formula × processing × test type × temperature (median) |
| `mpea_elong` | Elongation to failure (%) | MPEA database | rows with elongation, same keys and merging |
| `steel_uts` | Tensile strength (MPa) | `steel_strength` (matminer; Citrine steel data) | merged by composition (median) |
| `superhard_g` | Shear modulus (GPa) | Brgoch superhard training set | suspect values removed; merged by formula |
| `expt_gap` | Experimental band gap (eV) | Matbench `matbench_expt_gap` | merged by composition; whole chemical systems sampled (seed 0) to ≤ 4,000 rows, as for SuperCon |

**Dependence disclosure:**
- `mpea_uts` and `mpea_elong` share alloys with `mpea_ys` / `mpea_hv`.
- `steel_uts` shares compositions with `steel_ys`.
- `superhard_g` shares compounds with `superhard_k`.

These four test replication across *properties*. `expt_gap` is a fully independent material set.

## Protocol (identical to the exploratory study; no setting changes)
- Configuration: `config/default.yaml`, unchanged.
- Protocols random / system / cluster; 5 outer folds; seeds 0–9; α ∈ {0.05, 0.1, 0.2} (primary α = 0.1).
- Methods:
  - main set: SCP, CV+, CQR, WCP, GP, RF-z, Ens-z, GSCP;
  - all 10 CV+ variants, including FCP and FCP-W;
  - MCP, FCP-RFσ and CV+-RFσ.
- Chronological test for `mpea_uts` and `mpea_elong` (train on publications before 2019, test on 2019).

## Confirmatory hypotheses and decision rules
Unit of analysis: (task, shift protocol) cell, mean over 10 seeds. There are 5 tasks × 2 shift protocols = **10 new cells**, and the task level gives 5 units.

| ID | Hypothesis | Test | Success criterion |
|---|---|---|---|
| C1 | Random-calibrated SCP, CV+ and CQR under-cover under family shift | one-sided Wilcoxon of cell coverage vs 0.90 | p < 0.05 for each of the 3 methods |
| C2 | FCP's coverage shortfall is smaller than that of SCP, CV+, CQR and GSCP | two-sided Wilcoxon on paired shortfall, Holm over 4 | p_Holm < 0.05 for each |
| C3 | FCP's mean coverage is near nominal under shift | descriptive | mean coverage ≥ 0.88 in both shift protocols |
| C4 | **FCP-RFσ is near nominal under shift** | descriptive | mean coverage ≥ 0.88 in both shift protocols |
| C5 | **FCP-RFσ has a lower interval score than FCP** | two-sided Wilcoxon over the 10 cells | median difference < 0 and p < 0.05 |
| C6 | **FCP-RFσ is better calibrated in-distribution than RF-z** | random protocol, α = 0.2 and 0.1 | \|cov − nominal\| smaller for FCP-RFσ at both levels |

**Promotion rule (fixed in advance):**
- If C4, C5 and C6 all hold, FCP-RFσ is presented as the recommended variant, *confirmed on new tasks*.
- If any of them fails, it stays a post hoc observation and the failure is reported.
- C1–C3 failing would also be reported, with the abstract and conclusions revised accordingly.

**No re-runs, tuning or task substitutions** after results are seen. All tasks above are reported, whatever their outcome.
