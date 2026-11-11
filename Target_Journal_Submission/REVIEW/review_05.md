# Review Round 5 — Reviewer #5 (dataset validity, generalization, domain shift, external validity, deployment)

**Stance:** try to invalidate the central claim ("calibrating on whole held-out families restores coverage for alloys from unseen families"). Issues from Reviewers #1–#4 are not repeated.

## Attempts to invalidate the central claim

### 5.1 MAJOR: All shifts are synthetic
Every protocol constructs its shift by holding out families. Real deployment is chronological: a model trained on past literature predicts newly reported alloys, whose shift mixes family novelty with changes in processing, testing and reporting.

**Experiment added (stage `temporal`).** MPEA data, trained on publications before 2019 and tested on entries first reported in 2019 (the newest year). Rule fixed before running; 10 seeds; all methods.

**Pilot result (seed 0).** This is a *partial failure of the central claim*, and it is reported as such:
- *Yield strength:* 63% of the test alloys belong to unseen systems.
  - FCP coverage 0.899 overall and 0.901 on unseen systems.
  - SCP coverage 0.755 overall and 0.707 on unseen systems.
  - FCP works under a real chronological shift whose main component is family novelty.
- *Hardness:* **all methods fail** (SCP 0.656, CV+ 0.552, FCP 0.597).
  - The failure is concentrated in chemical systems *already present* in training (FCP 0.44 seen vs 0.77 unseen).
  - Predictions are biased by +83 HV.
  - The 2019 entries are harder on average (558 vs 462 HV) and are more often powder-processed or report no processing route.
  - This is a within-family concept or label shift that no calibration on historical data can anticipate.

**Manuscript change:** new Section 9.3 and Table "Chronological test", generated from `table_temporal.csv` with automated claim checks. The Discussion states the boundary of the method: it addresses novelty of the alloy family, not changes in how alloys of known families are made or measured. The full 10-seed numbers replace the pilot numbers automatically when the stage finishes.

### 5.2 MAJOR: Mis-specified family definition
With calibration on chemical systems but test shift to composition clusters, FCP falls from 0.902 to 0.814 (FCP-W 0.838). It remains the best method tested (SCP 0.700, CV+ 0.715, GSCP 0.763). The finding is prominent in Section 9.2 and the Discussion, together with a practical rule: calibrate on the coarser definition when in doubt.

### 5.3 MAJOR: Robustness to data quality and quantity
- Label noise of 0.10 / 0.25 SD(y) and training on only 50% of families (5 datasets × 5 seeds).
- FCP coverage: 0.923 / 0.920 / 0.922.
- SCP (0.864 / 0.868 / 0.840) and CV+ (0.878 / 0.883 / 0.865) remain below nominal.
- No degradation of FCP is observed (Section 9.1, Fig. "robustness").

### 5.4 MODERATE: Dataset representativeness
- MPEA entries come from many laboratories with heterogeneous processing and testing, only partly encoded.
- Steels: only 312 alloys.
- SuperCon: subsampled to about 4,000 compounds by whole systems.
- All three caveats are in the Limitations.
- The inorganic-compound tasks (bulk modulus, formation enthalpy, Tc) were included precisely to test external validity beyond alloys. Results are consistent across them (Table "summary").

### 5.5 MODERATE: Family threshold
The 1 at.% threshold that defines chemical systems is a modelling choice. The misspecification experiment (5.2) brackets its consequences: a finer family definition than the deployment shift costs coverage. A threshold sweep was not run and is noted as a limitation.

### 5.6 MINOR: Deployment practicality
FCP produces an interval for a new alloy immediately once the K fold models are trained (Section 10 reports the cost). It needs only compositions to define families, so no labels from the new family are required. This contrasts with recalibration on new-domain data (Morger et al.).

## Changes made
- New experiment and Section 9.3 (temporal), with an analysis splitting results by seen and unseen systems and a bias diagnostic.
- Section 9.2 (misspecification) and the revised Discussion paragraph "Choosing the family definition".
- Cross-references renumbered: Section 9.4 sensitivity, 9.5 base-learner swap, 9.6 random cluster assignment, 9.7 Mondrian.
- Limitations: the threshold sweep and within-family processing shift are added (Round 9 consolidates the limitations).

## Verdict after Round 5
The central claim survives in a **narrowed** form. Family-level calibration restores coverage when the deployment shift is family novelty, including a real chronological case. It does not protect against within-family changes in processing or measurement, and it degrades when the family definition is finer than the actual shift. The abstract and conclusions must state this boundary (to be implemented in Round 7, the writing review).
