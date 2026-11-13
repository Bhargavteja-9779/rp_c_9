# Supplementary Note S1: A finite-sample guarantee at the family level

## Setting (two-layer model; Dunn, Wasserman & Ramdas 2023)
- Families F₁, …, F_G, F_{G+1} are exchangeable random objects. Family g is a finite set of alloys {(x_{gj}, y_{gj})}, j = 1, …, n_g.
- Alloys within a family may be arbitrarily dependent, and n_g may vary.
- The test alloy (X, Y) is drawn uniformly at random from the alloys of the new family F_{G+1}.

## Family-subsampled FCP (FCP-S)
1. For every training family g ≤ G, draw one alloy (x̃_g, ỹ_g) uniformly from its alloys, independently of everything else. Write the unit as Z_g = (F_g, x̃_g, ỹ_g), and the test unit as Z_{G+1} = (F_{G+1}, X, Y).
2. Partition the G training families into K folds of equal size m = G/K.
3. For each fold k, fit μ_k and σ_k > 0 with an algorithm that receives *all alloys* of the families outside fold k. The algorithm must be invariant to the order in which families are presented. This holds for FCP: family-bagging, the k-NN novelty index and the scale model depend only on the set of training families. Fixing the random seeds of the algorithm makes it a deterministic, symmetric function of the set of units.
4. Compute R_g = |ỹ_g − μ_{k(g)}(x̃_g)| / σ_{k(g)}(x̃_g) for every training family.
5. Return the CV+ interval

   Ĉ(x) = [ q⁻_α{ μ_{k(g)}(x) − R_g σ_{k(g)}(x) }, q⁺_{1−α}{ μ_{k(g)}(x) + R_g σ_{k(g)}(x) } ],

   with unit weights over the G families. This is Eqs. (6)–(8) of the main text with one calibration alloy per family.

## Proposition 1
Under the assumptions above,

P( Y ∈ Ĉ(X) ) ≥ 1 − 2α − min{ 2(1 − 1/K)/(G/K + 1), (1 − K/G)/(K + 1) },

where the probability is over the families, the within-family draws and the test alloy.

**Proof.**
- The units Z₁, …, Z_{G+1} are exchangeable. The families are exchangeable, and each unit's alloy is an independent uniform draw within its own family; the test alloy is drawn the same way within F_{G+1}.
- Every quantity used by FCP-S is a function of the units. Each fold model is a symmetric function of the set of units it is trained on. Its training data are the whole families, which is allowed because a unit contains its entire family.
- FCP-S is therefore exactly the K-fold CV+ procedure of Barber et al. (2021, Theorem 4) applied to G exchangeable data points Z_g, with the nonconformity score s(z; f) = |ỹ − μ_f(x̃)| / σ_f(x̃).
- Barber et al.'s proof uses only two properties: the exchangeability of the data points (here, the units), and the inversion "y ∉ [μ − Rσ, μ + Rσ] ⟺ |y − μ|/σ > R", which holds for any σ > 0.
- The bound follows. ∎

## Remarks
1. **What is and is not covered.**
   - Proposition 1 covers FCP-S.
   - FCP-W replaces the single random draw per family by its expectation: every alloy of family g receives weight 1/n_g, so each family carries unit mass. This is the pooled-CDF construction of Dunn et al. (2023). It removes the variance of the random draw, but the proposition does not literally apply to it.
   - The unweighted FCP gives large families proportionally more weight. It targets alloy-level coverage and is not covered by Proposition 1 either. Both are evaluated empirically in the main text.
2. **Finite-G condition.** The weighted quantile in Eq. (8) is finite only if G/(G+1) ≥ 1 − α (Eq. 10). For α = 0.1 this requires G ≥ 9 training families.
3. **Why random-split calibration fails.** If calibration alloys are drawn at random, a calibration alloy usually shares its family with training alloys, while the test alloy does not. The calibration residuals are then not exchangeable with the test residual, and no guarantee of the above kind holds. Barber et al. (2023) bound the resulting coverage loss by the total-variation distance between the two score distributions, which can be large under family shift. Section 7 shows that it is large in practice.
4. **Practical size of the bound.** With G = 100 training families and K = 5 folds, the correction term is min{2(0.8)/21, 0.95/6} ≈ 0.076. The guarantee at α = 0.1 is then about 0.72, conservative as is typical for CV+. Empirically, CV+ and FCP cover close to 1 − α (Section 7).
