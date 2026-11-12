# Review Round 8 — Reviewer #8 (competing researcher)

**Stance:** I have developed similar uncertainty methods for materials and will try to show that the contribution is incremental, that an existing method already solves the problem, that the improvement comes from something else, that the baselines are unfair, or that the datasets favour the proposed approach. Earlier rounds' points are not repeated.

## Attack 1 — "An existing method already solves the problem: random-forest tree-spread intervals." (MAJOR)
**Evidence for the attack.** RF-z (μ ± z·SD over 300 trees) matches FCP's coverage under shift (0.950 / 0.914 vs 0.922 / 0.902). Its interval score is numerically better (12-cell median difference +0.15 SD in favour of RF-z; not significant).

**Author response — experiments run in this round:**
1. **Base-learner swap** (stage `basemodel`, seeds 0–4, all tasks and protocols). FCP with random-forest members covers 0.918 / 0.892, close to LightGBM-FCP at 0.923 / 0.899. Random-fold CV+ with the same forests fails at 0.866 / 0.743. *The calibration effect is model-independent.* FCP[RF] still had a worse interval score than RF-z (p = 0.0005).
2. **RF tree-spread normalization** (stage `rfsigma`; hypothesis written into the iteration log *before* the full run):
   - FCP-RFσ = family-grouped CV+ normalized by the forest's own tree spread.
   - Coverage: 0.920 / 0.912.
   - Interval score: statistically indistinguishable from RF-z (p = 0.68; better in 7 of 12 cells), and better than LightGBM-FCP in 11 of 12 cells (p = 0.0015).
   - **Calibrated in-distribution where RF-z is not:** 0.936 vs 0.954 at nominal 0.90, and 0.865 vs 0.909 at nominal 0.80.
   - The random-fold variant fails (0.888 / 0.813).

**Conclusion.** The attack is partly valid. RF tree spread is an excellent difficulty signal, and the paper now says so. But RF-z's coverage is uncalibrated over-width. The reviewer's own insight, combined with family-level calibration, yields the best calibrated method in the study. The manuscript reports this in Section 9.5, the Abstract, the Conclusions and the recommendations, and labels it as **post hoc**.

## Attack 2 — "The improvement is caused by wider intervals, not by better calibration." (MAJOR)
**Evidence against.** The comparisons do not rest on coverage alone:
- **Interval score** penalizes width. FCP beats SCP, CV+, CQR, GP, Ens-z and GSCP on it at the 12-cell level (Holm-corrected).
- **Ablation:** GCV+ (grouping only, no normalization) achieves most of the coverage gain. NCV+ (normalization only) does not. The gain comes from *which residuals* are used for calibration, not from a width multiplier.
- **Random protocol:** FCP over-covers modestly (0.941). This cost of conservativeness is reported, not hidden.

**No change needed** beyond the existing text.

## Attack 3 — "Baselines were weakened." (MODERATE)
- All conformal baselines share FCP's base learner, so differences in point accuracy cannot favour FCP.
- CQR reuses mean-regression hyper-parameters, the GP is capped at 800 training alloys, and RF-z uses scikit-learn defaults with max_features = 1/3. All of this is documented in Section 5.4.
- No method was tuned on test folds, FCP included.
- The strongest baseline, RF-z, is presented as a strong competitor and given its own section rather than being dismissed.

## Attack 4 — "The datasets favour the approach." (MODERATE)
- The datasets and family definitions were fixed in `research_design.md` before the main results.
- The design includes protocols *unfavourable* to FCP:
  - the random protocol, where FCP is conservative;
  - the mis-specified family definition, where FCP drops to 0.814;
  - the temporal hardness test, where every method fails.
- Three non-alloy tasks test external validity.

## Attack 5 — "Incremental: LOCO-CV + CV+." (MODERATE)
Answered in Round 2. The present round adds a further argument: the obvious "simpler" alternatives were each tested and each fails under family shift. These are density-ratio weighting, Mondrian conditioning on novelty (MCP 0.767 under cluster holdout), recalibration of σ on random folds (NCV+), and random-fold calibration of tree spread (CV+-RFσ). The specific ingredient, calibration on whole held-out families, is necessary and is the source of the effect.

## Changes in this round
- New Section 9.5 paragraph and verdict generated from data, with claim checks:
  - FCP-RFσ coverage ≥ 0.9 in both shift protocols;
  - interval score not different from RF-z;
  - interval score better than FCP;
  - better calibrated than RF-z in-distribution.
- Abstract (246 words), Conclusion item 4 and the Discussion recommendation updated.
- `supplementary/iteration_log.md`: outcome recorded beneath the pre-registered hypothesis.
