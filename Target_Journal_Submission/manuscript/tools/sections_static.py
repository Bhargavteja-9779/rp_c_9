"""Manuscript sections that do not depend on experimental numbers (Introduction, Related work, Gap, Method, Setup).
Numbers that come from the data (dataset sizes etc.) are injected from machine-generated tables via V."""

CITE_KEYS = {
    "vovk2005": "10.1007/b106715", "lei2018": "10.1080/01621459.2017.1307116", "barber2021": "10.1214/20-AOS1965",
    "dunn2023": "10.1080/01621459.2022.2060112", "barber2023": "10.1214/23-AOS2276", "papadopoulos2011": "10.1613/jair.3198",
    "angelopoulos2023": "10.1561/2200000101", "ward2016": "10.1038/npjcompumats.2016.28", "ward2018": "10.1016/j.commatsci.2018.05.018",
    "ong2013": "10.1016/j.commatsci.2012.10.028", "borg2020": "10.1038/s41597-020-00768-9", "hamidieh2018": "10.1016/j.commatsci.2018.07.052",
    "dunn2020": "10.1038/s41524-020-00406-3", "tehrani2018": "10.1021/jacs.8b02717", "kingsbury2022": "10.1038/s41524-022-00881-w", "zhuo2018": "10.1021/acs.jpclett.8b00124",
    "meredig2018": "10.1039/C8ME00012C", "breiman2001": "10.1023/A:1010933404324", "gneiting2007": "10.1198/016214506000001437",
    "tran2020": "10.1088/2632-2153/ab7e1a", "palmer2022": "10.1038/s41524-022-00794-8", "varivoda2023": "10.1063/5.0133528",
    "akdogan2026": "10.1021/acsomega.6c02607", "han2026": "10.3390/polym18192445", "omee2024": "10.1038/s41524-024-01316-4",
    "ling2017": "10.1007/s40192-017-0098-z", "wen2019": "10.1016/j.actamat.2019.03.010", "rao2022": "10.1126/science.abo4940",
    "lookman2019": "10.1038/s41524-019-0153-8", "miracle2017": "10.1016/j.actamat.2016.08.081", "xiong2020": "10.1016/j.commatsci.2019.109203",
    "hirschfeld2020": "10.1021/acs.jcim.0c00502", "bhattacharyya2026": "10.1214/26-EJS2506", "gibbs2025": "10.1093/jrsssb/qkaf008",
    "fannjiang2022": "10.1073/pnas.2204569119", "johansson2014": "10.1007/s10994-014-5453-0", "vovk2015": "10.1007/s10472-013-9368-4",
    "segal2025": "10.1038/s41524-025-01808-x", "morger2021": "10.1186/s13321-021-00511-5",
    "morger2022": "10.1038/s41598-022-09309-3", "guo2011": "10.1063/1.3587228", "zhang2008": "10.1002/adem.200700240",
    "wang2012": "10.1016/j.intermet.2012.03.005",
}
MANUAL = {
    "romano2019": "Y. Romano, E. Patterson, E.J. Candès, Conformalized quantile regression, in: Advances in Neural Information "
                  "Processing Systems 32 (NeurIPS 2019), 2019. arXiv:1905.03222.",
    "tibshirani2019": "R.J. Tibshirani, R. Foygel Barber, E.J. Candès, A. Ramdas, Conformal prediction under covariate shift, in: "
                      "Advances in Neural Information Processing Systems 32 (NeurIPS 2019), 2019. arXiv:1904.06019.",
    "tan2025": "L. Tan, P. Chen, M. Liu, X. Wang, J. Cen, Q. Zou, Benchmarking GNNs for OOD materials property prediction with "
               "uncertainty quantification, arXiv preprint arXiv:2511.11697, 2025.",
    "boruah2026": "I. Boruah, Distribution-free conformal prediction for steel fatigue strength: marginal validity is not enough, "
                  "arXiv preprint arXiv:2608.07589, 2026.",
    "ke2017": "G. Ke, Q. Meng, T. Finley, T. Wang, W. Chen, W. Ma, Q. Ye, T.-Y. Liu, LightGBM: a highly efficient gradient boosting "
              "decision tree, in: Advances in Neural Information Processing Systems 30 (NIPS 2017), 2017, pp. 3146–3154.",
    "pedregosa2011": "F. Pedregosa, G. Varoquaux, A. Gramfort, V. Michel, B. Thirion, O. Grisel, M. Blondel, P. Prettenhofer, R. Weiss, "
                     "V. Dubourg, J. Vanderplas, A. Passos, D. Cournapeau, M. Brucher, M. Perrot, E. Duchesnay, Scikit-learn: "
                     "machine learning in Python, J. Mach. Learn. Res. 12 (2011) 2825–2830.",
    "rasmussen2006": "C.E. Rasmussen, C.K.I. Williams, Gaussian Processes for Machine Learning, MIT Press, Cambridge, MA, 2006.",
}


def intro(V):
    return [
        ("h1", "1. Introduction"),
        ("p", "Machine-learning (ML) models that map alloy composition and processing to properties are now routinely used to "
              "screen candidate alloys before synthesis, including high-entropy and other multi-principal-element alloys (MPEAs) "
              "[@wen2019;@rao2022;@miracle2017]. The candidates of greatest interest are usually *not* close relatives of the "
              "alloys in the training data: a design campaign typically moves into chemical systems, or regions of composition "
              "space, that have never been measured. For such decisions a point prediction is insufficient. An alloy designer "
              "needs an interval that contains the true property with a stated probability, so that design margins, screening "
              "thresholds and experimental budgets can be set rationally [@lookman2019;@ling2017]."),
        ("p", "Conformal prediction converts any point predictor into prediction intervals with a finite-sample, distribution-free "
              "coverage guarantee [@vovk2005;@lei2018;@angelopoulos2023]. The guarantee rests on one assumption: the calibration "
              "data and the new case must be exchangeable. In the usual workflow, calibration alloys are drawn at random from "
              "the same database as the training alloys. When the new alloy belongs to a family that is absent from that "
              "database, exchangeability fails at precisely the point where the prediction is most needed [@barber2023]. "
              "Materials studies have shown that randomly split cross-validation overstates accuracy for new chemistries "
              "[@meredig2018;@xiong2020;@omee2024;@tan2025]. Recent work on polymers has shown that split-conformal coverage "
              "falls well below nominal when whole chemical classes are held out [@han2026;@akdogan2026]. For "
              "composition-based alloy property models, however, the size of this coverage loss has not been quantified, and no "
              "calibration procedure has been proposed and tested that restores coverage when the test alloy comes from an unseen "
              "alloy family."),
        ("p", "This paper addresses that gap. We treat the *alloy family* (the chemical system of an alloy, or a cluster of "
              "similar compositions) as the unit of exchangeability, following the hierarchical view of Dunn et al. "
              "[@dunn2023]. On this basis we construct **family-calibrated conformal prediction (FCP)**. FCP calibrates a "
              "cross-validation-plus (CV+) interval [@barber2021] on residuals of whole held-out families. The scores are "
              "normalized by a scale that grows with ensemble disagreement and compositional novelty, and the scale model is "
              "fitted only on family-out-of-bag residuals, so calibration labels are never reused. A family-weighted variant "
              "(FCP-W) targets equal coverage across families instead of across alloys. We evaluate both against eight "
              "established interval methods on six public datasets, under three split protocols of increasing extrapolation "
              "difficulty. None of the ingredients is new on its own: grouped cross-validation, CV+, normalized scores and "
              "hierarchical exchangeability are all established. What this work adds is their combination for the alloy-family "
              "deployment shift, an explicit statement of what is (and is not) guaranteed, a scale model that cannot leak "
              "calibration labels, and evidence across datasets of how large the problem is and which component solves it."),
        ("p", "The contributions are:"),
        ("bullets", [
            "A calibration procedure, FCP / FCP-W, whose calibration step reproduces the deployment shift of alloy design "
            "(prediction for an unseen alloy family). It states its estimand explicitly (alloy-level vs family-level coverage) "
            "and the finite-sample condition under which the family-level interval is finite (Section 4).",
            "A benchmark of interval coverage under alloy-family extrapolation: "
            f"{V['n_tasks']} tasks, 3 split protocols, {V['n_seeds']} outer-split seeds and 17 interval methods. It shows how far "
            "random-split calibration and model-based uncertainty fall below nominal coverage (Section 7).",
            "Evidence of the practical consequence for alloy screening (false discoveries among lower-bound selections) and a "
            "chronological deployment test that delineates what family-level calibration can and cannot correct (Sections 7.5 "
            "and 9.3).",
            "Ablation, robustness, sensitivity and efficiency experiments that isolate which component matters and what it costs, "
            "together with an error analysis of the alloy families on which intervals still fail (Sections 8–11).",
            "A fully reproducible code base in which every number, table and figure is regenerated from public data by a single "
            "command.",
        ]),
    ]


def related(V):
    return [
        ("h1", "2. Related work"),
        ("h2", "2.1. Uncertainty quantification for materials property models"),
        ("p", "Uncertainty estimates for materials ML are most often model-based. They include the spread of random-forest "
              "trees or bootstrap ensembles [@breiman2001;@ling2017], Gaussian-process (GP) posterior variances "
              "[@rasmussen2006], and the dispersion of neural-network ensembles, Monte-Carlo dropout or evidential heads "
              "[@hirschfeld2020;@varivoda2023;@tan2025]. Comparative studies report that such estimates are frequently "
              "miscalibrated, and they recommend recalibrating them on held-out data [@tran2020;@palmer2022]. Recalibration "
              "uses randomly held-out data, however, so it inherits the exchangeability problem examined here. Benchmarks of "
              "out-of-distribution (OOD) prediction for crystal structures [@omee2024;@tan2025] and for out-of-range property "
              "values [@segal2025] document accuracy losses and moderate uncertainty–error correlations. They do not evaluate "
              "the coverage of prediction intervals."),
        ("h2", "2.2. Conformal prediction in materials science"),
        ("p", "Conformal prediction has recently been applied to materials data. Boruah [@boruah2026] used split, normalized, "
              "Mondrian and quantile-based conformal methods for the fatigue strength of steels. That study showed that marginal "
              "validity can hide under-coverage in the highest-strength quartile, but all of its evaluations used random splits "
              "of a single dataset. For polymers, Akdoğan [@akdogan2026] and Han et al. [@han2026] evaluated split conformal "
              "prediction under scaffold, cluster and class holdouts. Han et al. reported that coverage fell from 0.899 under "
              "random splits to 0.683 under class holdout, and that a similarity-based applicability gate gave little "
              "protection. Neither study proposed a calibration procedure that restores coverage under the holdout. The closest "
              "precedent is in cheminformatics. Morger et al. [@morger2021;@morger2022] observed that conformal predictors for "
              "toxicity lost validity on temporally later or external data, and that exchanging the calibration set for data "
              "resembling the new domain restored validity without retraining. That remedy requires *labelled* data from the "
              "shifted domain. In alloy discovery such data do not exist until the new family has been synthesized and tested. "
              "The approach studied here instead constructs the shift *inside* the training data, by calibrating on whole "
              "held-out families."),
        ("h2", "2.3. Conformal prediction beyond exchangeability"),
        ("p", "Statistical work offers several routes beyond exchangeability. Weighted conformal prediction reweights "
              "calibration scores by an estimated density ratio under covariate shift [@tibshirani2019;@fannjiang2022]. Bounds "
              "on the coverage lost under non-exchangeability are available [@barber2023]. Methods also exist that target "
              "conditional or group-wise coverage [@gibbs2025;@bhattacharyya2026]. Dunn et al. [@dunn2023] studied two-layer "
              "hierarchical data, in which groups are exchangeable but observations within a group are not exchangeable with "
              "those of other groups, and constructed prediction sets for observations from a *new* group. Locally adaptive "
              "(normalized) conformal scores [@papadopoulos2011;@lei2018;@johansson2014] and cross-conformal / CV+ constructions "
              "[@vovk2015;@barber2021] make intervals adaptive and data-efficient. To our knowledge these tools have not been "
              "combined and tested for the alloy-family extrapolation problem."),
    ]


def gap(V):
    return [
        ("h1", "3. Research gap and motivation"),
        ("p", "Three observations motivate this work. (i) Alloy design is an extrapolation problem at the level of *families*: "
              "new chemical systems, or new regions of composition space. (ii) The standard calibration step of conformal "
              "prediction draws calibration alloys at random, so it measures interpolation error. Its guarantee therefore does "
              "not transfer to new families, and the size of the resulting shortfall for alloy property models is unknown. "
              "(iii) Weighted conformal prediction corrects covariate shift only when the test distribution has support inside "
              "the calibration distribution. A genuinely new chemical system violates that condition, so it is unclear whether "
              "density-ratio weighting helps."),
        ("p", "We therefore ask five research questions. **RQ1**: do random-calibrated conformal methods and model-based "
              "intervals keep their nominal coverage on unseen chemical systems and composition clusters? **RQ2**: does family-"
              "level calibration close the coverage shortfall, and at what cost in interval width? **RQ3**: which component of "
              "FCP is responsible: grouping, normalization or weighting? **RQ4**: is the procedure robust to label noise, smaller "
              "training sets, the miscoverage level and its own hyper-parameters? **RQ5**: does it generalize across datasets and "
              "shift types, including a mis-specified family definition? Each question is answered by a pre-specified experiment "
              "(Section 6), and the design was fixed before the main results were inspected."),
    ]


def method(V):
    E = []
    E += [
        ("h1", "4. Proposed method: family-calibrated conformal prediction"),
        ("h2", "4.1. Problem formulation"),
        ("p", "Let *D* = {(*x*_{i}, *y*_{i}, *g*_{i})}, *i* = 1, …, *n*, be the training data. Here *x*_{i} describes the "
              "composition (and, where available, the processing and test conditions) of alloy *i*, *y*_{i} is the measured "
              "property, and *g*_{i} ∈ {1, …, *G*} is the alloy family to which the composition belongs. Families are defined "
              "from composition alone (Section 5.2), so the family of a new alloy is known before it is measured. A new alloy "
              "*x*_{n+1} is drawn from a family *g*_{n+1} that does not occur in *D*. For a miscoverage level α we seek an "
              "interval Ĉ(*x*) with"),
        ("eq", ["P", {"paren": [{"sub": ["Y", "n+1"]}, " ∈ ", "Ĉ", {"paren": [{"sub": ["X", "n+1"]}]}]}, " ≥ 1 − α"]),
        ("p", "where the probability is taken over a new family and an alloy within it. Following Dunn et al. [@dunn2023], we "
              "regard the families as exchangeable units, while alloys of one family may be arbitrarily dependent. Eq. (1) then "
              "describes alloy-level coverage on unseen families. The family-level estimand averages coverage over families "
              "with equal weight."),
        ("h2", "4.2. Family-bagged base predictor and difficulty signals"),
        ("p", "The point predictor is an ensemble of *M* gradient-boosted tree regressors (LightGBM [@ke2017]). Member *m* is "
              "trained on the alloys of a random subset containing a fraction φ of the families (row subsampling is used instead "
              "if fewer than three families are available). Family subsampling has two "
              "purposes. First, the member spread"),
        ("eq", [{"sub": ["μ", "k"]}, "(x) = ", {"frac": [["1"], ["M"]]}, "∑", {"sub": ["f", "k,m"]}, "(x),    ",
                {"sub": ["s", "k"]}, "(x) = sd", {"sub": [{"curly": [{"sub": ["f", "k,m"]}, "(x)"]}, "m=1..M"]}]),
        ("p", "measures how much the prediction depends on which families were seen. Second, every training alloy has "
              "*family-out-of-bag* (FOOB) predictions, made only by the members that did not see its family. These mimic the "
              "error made on a new family. In Eq. (2) the index *k* denotes the inner cross-fitting fold whose training part "
              "the ensemble was fitted on (Section 4.3). A second difficulty signal is compositional novelty. It is the mean "
              "Euclidean distance from *x* to its *k*_{nn} nearest training alloys in a standardized, principal-component-reduced "
              "feature space:"),
        ("eq", [{"sub": ["d", "k"]}, "(x) = ", {"frac": [["1"], [{"sub": ["k", "nn"]}]]}, {"sub": ["∑", "j ∈ N_k(x)"]}, "‖z(x) − z(",
                {"sub": ["x", "j"]}, ")‖"]),
        ("p", "For a training alloy, FOOB novelty is computed against alloys of *other* families only."),
        ("h2", "4.3. Normalized scores with a leakage-free scale model"),
        ("p", "Scores are normalized by a difficulty scale σ_{k}(*x*), which is log-linear in the two signals and constrained "
              "to be non-decreasing in each:"),
        ("eq", ["log ", {"sub": ["σ", "k"]}, "(x) = ", {"sub": ["a", "k"]}, " + ", {"sub": ["b", "k"]}, " log ", {"sub": ["s", "k"]},
                "(x) + ", {"sub": ["c", "k"]}, " log ", {"sub": ["d", "k"]}, "(x),    ", {"sub": ["b", "k"]}, ", ",
                {"sub": ["c", "k"]}, " ≥ 0"]),
        ("p", "The coefficients are fitted by bounded least squares of log|FOOB residual| on the two log-signals. The fit uses "
              "*only* the training part *D*_{−k} of fold *k*: the spread entering the fit is the FOOB spread (standard deviation "
              "over the members that did not see the alloy's family) and the novelty is the FOOB novelty. If ten or fewer alloys "
              "have FOOB residuals, σ_{k} ≡ 1. When σ_{k} is evaluated, both signals are clamped to the range observed in the fit, "
              "so the log-linear model is never extrapolated, and σ_{k} is floored at the 5th percentile of its fitted values. The "
              "non-negativity constraints encode a physical prior: larger model disagreement or greater compositional distance "
              "should never *narrow* an interval. Because the scale model never sees the labels of fold *k*, the normalized score"),
        ("eq", [{"sub": ["S", "i"]}, " = ", {"abs": [{"sub": ["y", "i"]}, " − ", {"sub": ["μ", "k(i)"]}, "(", {"sub": ["x", "i"]}, ")"]}, " / ",
                {"sub": ["σ", "k(i)"]}, "(", {"sub": ["x", "i"]}, ")"]),
        ("p", "of a calibration alloy *i* in fold *k*(*i*) is computed exactly as a test score would be."),
        ("h2", "4.4. Family-grouped CV+ interval"),
        ("p", "The training families are partitioned at random into *K* folds. No family is split across folds. For each fold, "
              "the ensemble, novelty scorer and scale model are fitted on the other *K* − 1 folds, and the scores of Eq. (5) are "
              "computed on the held-out families. A new alloy then receives the CV+ interval [@barber2021], with weights:"),
        ("eq", ["L(x) = ", {"subsup": ["Q", "α", "lo"]}, {"brack": [{"sub": ["μ", "k(i)"]}, "(x) − ", {"sub": ["S", "i"]}, " ",
                                                                  {"sub": ["σ", "k(i)"]}, "(x)"]}]),
        ("eq", ["U(x) = ", {"subsup": ["Q", "1−α", "hi"]}, {"brack": [{"sub": ["μ", "k(i)"]}, "(x) + ", {"sub": ["S", "i"]}, " ",
                                                                    {"sub": ["σ", "k(i)"]}, "(x)"]}]),
        ("p", "so that Ĉ(*x*) = [*L*(*x*), *U*(*x*)]. Here the brackets denote the multiset of *n* values, one per training alloy "
              "*i*, and the weighted upper quantile of values *v*_{i} with weights *w*_{i} is"),
        ("eq", [{"subsup": ["Q", "β", "hi"]}, " = inf", {"curly": ["t : ∑ ", {"sub": ["w", "i"]}, " 1[", {"sub": ["v", "i"]}, " ≤ t] ≥ β ",
                                                                  {"paren": ["∑ ", {"sub": ["w", "i"]}, " + ", {"sub": ["w", "∞"]}]}]}]),
        ("p", "where the sum runs over the training alloys and the extra mass *w*_{∞} sits at +∞. *Q*^{lo}_{α} is the corresponding lower quantile, with *w*_{∞} placed at −∞. Two weighting "
              "schemes define the two estimands:"),
        ("eq", ["FCP: ", {"sub": ["w", "i"]}, " = 1;     FCP-W: ", {"sub": ["w", "i"]}, " = ", {"frac": [["1"], [{"sub": ["n", "g(i)"]}]]},
                ";     ", {"sub": ["w", "∞"]}, " = 1"]),
        ("p", "where *n*_{g} is the number of training alloys of family *g*. With unit weights, Eqs. (6)–(7) give the normalized CV+ "
              "interval with family-grouped folds, and it targets alloy-level coverage on new families. With weights 1/*n*_{g}, "
              "every training family carries unit mass and the test alloy is treated as one new family. This is the pooled "
              "construction of Dunn et al. [@dunn2023], and it targets family-level coverage. A finite-sample consequence is "
              "that the upper quantile of Eq. (8) is finite only if *G*/(*G* + 1) ≥ 1 − α, that is"),
        ("eq", ["G ≥ ", {"frac": [["1 − α"], ["α"]]}, "    (G ≥ 9 for α = 0.1)"]),
        ("p", "With fewer training families, FCP-W correctly returns an unbounded interval: so few families cannot certify a "
              "90% family-level statement. We report this case explicitly rather than hiding it."),
        ("p", "**Finite-sample guarantee at the family level.** A guarantee follows if each family contributes a single, "
              "randomly drawn calibration alloy (family-subsampled FCP, FCP-S). Let the families be exchangeable, let each fold "
              "model depend on the set of training families symmetrically, and let the test alloy be drawn uniformly from a new "
              "family. Then each unit (family, sampled alloy) is exchangeable with the test unit, and FCP-S is exactly the "
              "*K*-fold CV+ procedure of Barber et al. [@barber2021] applied to *G* data points with the normalized score of Eq. (5). "
              "Hence"),
        ("eq", ["P", {"paren": ["Y ∈ Ĉ(X)"]}, " ≥ 1 − 2α − min", {"curly": [{"frac": [["2(1 − 1/K)"], ["G/K + 1"]]}, ", ",
                                                                        {"frac": [["1 − K/G"], ["K + 1"]]}]}]),
        ("p", "(Proposition 1; proof in Supplementary Note S1). FCP-W replaces the single random draw by its expectation "
              "(weights 1/*n*_{g}), which is the pooled construction of Dunn et al. [@dunn2023]. The unweighted FCP targets "
              "alloy-level coverage. Neither is literally covered by Proposition 1, so both are assessed empirically below. "
              "Proposition 1 also explains why random-split calibration fails: a randomly held-out calibration alloy shares its "
              "family with training alloys, so its score is not exchangeable with that of an alloy from a new family, and the "
              "coverage loss is bounded only by the distance between the two score distributions [@barber2023]."),
        ("h2", "4.5. Algorithm and complexity"),
        ("p", "FCP requires *K* ensembles of *M* members, i.e. *KM* tree-ensemble fits, plus *K* nearest-neighbour indices. "
              "Forming the interval for *n*_{t} test alloys costs O(*n*_{t} *n* log *n*) for sorting the *n* candidate bounds per "
              "test alloy. Random-split CV+ has the same cost. Split conformal prediction requires *M* fits but uses only part of "
              "the data for training. Measured costs are reported in Section 10. Fig. {fig:workflow} summarizes the procedure."),
        ("fig", ("fig1_workflow", "Fig. {fig:workflow}. Family-calibrated conformal prediction (FCP). Training alloys are split "
                 "into folds that never share a family (Step 1); each fold's family-bagged ensemble, novelty scorer and scale model "
                 "are fitted without the fold (Step 2); scores of the held-out families (Step 3) form weighted CV+ quantiles around "
                 "each fold model's prediction (Step 4).")),
    ]
    return E


def setup(V):
    return [
        ("h1", "5. Experimental setup"),
        ("h2", "5.1. Datasets"),
        ("p", "Six regression tasks from public sources were used (Table {tab:datasets}). Two come from the MPEA database of Borg et al. "
              "[@borg2020]: Vickers hardness, and yield strength with test temperature, test type (tension/compression) and "
              "processing route as additional inputs. One is the yield strength of 312 steels from Matbench [@dunn2020]. "
              "Three are inorganic-compound tasks, used to test generalization beyond alloys: the bulk modulus training set of "
              "Mansouri Tehrani et al. [@tehrani2018] (rows flagged as suspect removed), experimental formation enthalpies "
              "compiled by Kingsbury et al. [@kingsbury2022], and superconducting critical temperatures from the SuperCon-derived "
              "dataset of Hamidieh [@hamidieh2018]. Identical inputs (same formula and, for MPEA tasks, same processing and test "
              "conditions) were merged by the median target before any split. The superconductor set was reduced to "
              f"{V['supercon_n']} compounds by sampling whole chemical systems with a fixed seed, to fit the computational "
              "budget. Fig. {fig:datasets} shows the target distributions and the strongly skewed sizes of the chemical-system "
              "families: most systems contain one or a few alloys, a few contain dozens."),
        ("table1", None),
        ("fig", ("fig2_dataset_distributions", "Fig. {fig:datasets}. Target distributions (top) and number of alloys per chemical "
                 "system (bottom, logarithmic axis) for the six tasks.")),
        ("h2", "5.2. Features and alloy families"),
        ("p", "Each composition was described by the 132 Magpie elemental-property statistics [@ward2016], computed with "
              "matminer [@ward2018] and pymatgen [@ong2013], together with the atomic fraction of every element present in the "
              "task. For the MPEA tasks, one-hot processing route and test type and the numeric test temperature were added. "
              "Constant columns were removed. No feature uses the target. Two family definitions were used. **F1 (chemical "
              "system)**: the set of elements present at ≥ 1 at.%, so that trace additions in steels do not create spurious "
              "systems. **F2 (composition cluster)**: *k*-means with *k* = 10 on atomic-fraction vectors, in the spirit of "
              "leave-one-cluster-out cross-validation [@meredig2018]."),
        ("h2", "5.3. Evaluation protocols"),
        ("p", "Each task was evaluated with five outer folds under three protocols. **Random**: rows grouped by formula, an "
              "in-distribution control. **System**: whole F1 families held out. **Cluster**: whole F2 clusters held out, the "
              "hardest extrapolation. Every outer test alloy was predicted exactly once per seed. Ten seeds (0–9, fixed in "
              "advance) re-randomized the outer folds and all internal randomness. Every method was fitted and calibrated on "
              "the outer training part only. Grouped methods used the families of the protocol internally (F1 in the random "
              "protocol). Experiment 5 deliberately mis-specifies this choice."),
        ("h2", "5.4. Compared methods"),
        ("p", "All methods share the same family-bagged LightGBM base learner (Section 4.2), so differences reflect "
              "calibration rather than accuracy, except for the GP and random-forest baselines, which have their own models. "
              "Random-calibrated conformal baselines: split conformal prediction (**SCP**, 75/25 random split [@lei2018]); "
              "CV+ with random folds (**CV+** [@barber2021]); normalized CV+ with random folds (**NCV+**, the conformal analogue of recalibrating ensemble "
              "uncertainties on randomly held-out data [@palmer2022], and of the normalized method of [@boruah2026]); "
              "conformalized quantile regression with LightGBM quantile models "
              "(**CQR** [@romano2019]); and weighted split conformal prediction with a logistic-regression density-ratio "
              "estimate between calibration and test features (**WCP** [@tibshirani2019]); and Mondrian split conformal prediction "
              "with separate calibration quantiles in tertiles of compositional novelty (**MCP** [@vovk2005], Section 9). "
              "Model-based intervals: a GP with an "
              "automatic-relevance-determination RBF kernel plus white noise on 16 principal components (**GP** "
              f"[@rasmussen2006], at most {V['gp_max']} training alloys); random-forest tree spread [@breiman2001] (**RF-z**, "
              "μ ± *z*·*s*); and the base ensemble's member spread (**Ens-z**). Family-calibrated baseline: split conformal "
              "prediction with 25% of the training *families* held out for calibration (**GSCP**), the simplest way to "
              "calibrate on new families. Proposed: **FCP** and **FCP-W**. Ablations (Section 8) vary grouping, the scale model "
              "(none / spread / novelty / both) and weighting within the same CV+ code path (10 variants). Deviations from the "
              "original descriptions of the baselines, made to keep a common base learner and budget, were as follows. CQR used "
              "LightGBM quantile regressors with the same hyper-parameters as the point model. WCP estimated density ratios with "
              "an L2-regularized logistic-regression classifier on 16 principal components. The GP was trained on at most "
              f"{V['gp_max']} alloys (a random subset for the three larger tasks). RF-z used 300 trees with max_features = 1/3. "
              "No baseline was tuned on test folds, and neither was FCP."),
        ("h2", "5.5. Metrics and statistical analysis"),
        ("p", "For each run the following were recorded:"),
        ("bullets", [
            "empirical coverage, the fraction of test alloys inside their interval, and family coverage, the mean of "
            "within-family coverage;",
            "the mean finite interval width divided by the standard deviation of *y*, and the fraction of infinite intervals;",
            "the Winkler interval score [@gneiting2007], IS_{α} = (*u* − *l*) + (2/α)(*l* − *y*)·1{*y* < *l*} + "
            "(2/α)(*y* − *u*)·1{*y* > *u*}, divided by SD(*y*), which rewards narrow intervals and penalizes misses;",
            "coverage within tertiles of test-alloy novelty;",
            "the R² of the shared point predictor.",
        ]),
        ("p", "The primary level was α = 0.1, with α = 0.05 and 0.2 secondary. The unit of statistical analysis is a cell: one "
              "task under one shift protocol, averaged over the ten seeds. Seeds re-partition the same data, so they describe "
              "split-to-split variability, not independent replicates. Pre-specified hypotheses were tested with Wilcoxon "
              "signed-rank tests over the 12 shift cells (6 tasks × 2 shift protocols), and Holm correction was applied across "
              "the eight baselines. H1 tested one-sided under-coverage of random-calibrated methods against 0.90. H2 tested "
              "FCP against each baseline on the coverage shortfall max(0, 0.9 − coverage). H3 tested the same comparisons on "
              "the interval score. Effect sizes are matched-pairs rank-biserial correlations, and 95% confidence intervals for "
              "the median paired difference were obtained by bootstrap (10,000 resamples). The two shift protocols of a task "
              "share data, so the 12 cells are not fully independent. Each test is therefore also reported separately per "
              "protocol (6 cells), and at the task level (6 independent units, each averaging its two shift protocols). The "
              "families of F2 are obtained by unsupervised clustering of compositions of all alloys in a task. This uses no "
              "target values, and the definition of what counts as 'new' is fixed before any split."),
        ("h2", "5.6. Implementation"),
        ("p", f"Pre-specified settings: LightGBM with {V['lgbm_trees']} trees, learning rate {V['lgbm_lr']}, {V['lgbm_leaves']} leaves, "
              f"row and column subsampling {V['lgbm_sub']} and {V['lgbm_col']}, minimum 5 alloys per leaf, L2 penalty 1; *M* = {V['M']} members; φ = {V['phi']}; *K* = {V['K']} "
              f"inner folds; *k*_{{nn}} = {V['knn']}; {V['pcs']} principal components. None of these was tuned on test folds, and "
              "their influence is examined in Section 9.6. All computations ran on CPUs (4 cores, no GPU) with Python, "
              "scikit-learn [@pedregosa2011] and LightGBM. A single command (run_all.py) regenerates every number, table and "
              "figure from the public data."),
    ]
