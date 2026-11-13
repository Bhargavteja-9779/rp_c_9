"""Builds the manuscript spec (JSON) from machine-generated results; node build_docx.js renders it to DOCX.

All numbers are read from code/results (CSV/JSON). Directional claims in the text are verified by `claim()`;
if a claim no longer holds (e.g. after re-running experiments) the build fails instead of printing a wrong sentence.
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "code" / "results"
TAB, FIG = RES / "tables", RES / "figures"
sys.path.insert(0, str(HERE))
from mdocx import runs, Bib, load_bib
import sections_static as S
import yaml

CLAIMS = []
# Supplementary figures (numbering shared with build_supplementary.py)
SUPP_FIGS = [("alpha", "fig11_alpha_calibration", "Empirical versus nominal coverage at α ∈ {0.05, 0.1, 0.2} for key methods, averaged over datasets."),
             ("sens", "fig10_sensitivity", "Coverage of FCP and FCP-W under one-factor-at-a-time variation of K, M, φ and k_nn (three alloy tasks, unseen-system protocol, five seeds); circled points are the pre-specified defaults."),
             ("efficiency", "fig12_efficiency", "Wall time and peak memory for one outer fold (unseen-system protocol, single process)."),
             ("parity", "fig7_parity_intervals_mpea_hv", "Measured versus predicted MPEA hardness with 90% intervals for test alloys from unseen composition clusters (seed 0): SCP (left) and FCP (right).")]
SFIG = {k: f"S{i + 1}" for i, (k, _, _) in enumerate(SUPP_FIGS)}


def claim(cond, text):
    CLAIMS.append({"claim": text, "holds": bool(cond)})
    if not cond:
        raise AssertionError("Claim not supported by results: " + text)


RC = ["SCP", "CV+", "CQR", "WCP"]  # random-calibrated conformal methods (defines every reported range)


def rc_range(V, prot, pct=True):
    v = [V["g"](prot, m) for m in RC]
    lo, hi = min(v), max(v)
    return f"{lo * 100:.0f}–{hi * 100:.0f}%" if pct else f"{lo:.2f}–{hi:.2f}"


def f3(x):
    return "∞" if np.isinf(x) else f"{x:.3f}"


def f2(x):
    return "∞" if np.isinf(x) else f"{x:.2f}"


def load():
    cfg = yaml.safe_load(open(ROOT / "code" / "config" / "default.yaml"))
    raw = pd.read_csv(RES / "raw_results.csv")
    df = raw[~raw.method.str.endswith(" (v1)")]
    summ = pd.read_csv(TAB / "table_summary_by_protocol.csv")
    cm = pd.read_csv(TAB / "cell_means_alpha0.1.csv")
    st = json.load(open(RES / "statistics.json"))
    ds = pd.read_csv(TAB / "dataset_summary.csv")
    V = {"cfg": cfg, "df": df, "summ": summ, "cm": cm, "st": st, "ds": ds}
    V["n_tasks"] = df.task.nunique(); V["n_seeds"] = df.seed.nunique()
    V["supercon_n"] = int(ds[ds.task == "supercon_tc"].n.iloc[0])
    V["gp_max"] = cfg["gp_max_train"]
    lp = cfg["lgbm_params"]
    V.update(lgbm_trees=lp["n_estimators"], lgbm_lr=lp["learning_rate"], lgbm_leaves=lp["num_leaves"], lgbm_sub=lp["subsample"],
             lgbm_col=lp["colsample_bytree"], M=cfg["n_members"], phi=cfg["family_frac"], K=cfg["K"], knn=cfg["novelty_k"],
             pcs=cfg["novelty_pcs"])

    def g(p, m, col="mean_coverage"):
        s = summ[(summ.protocol == p) & (summ.method == m)]
        return float(s[col].iloc[0])
    V["g"] = g
    V["n_runs"] = int(raw.groupby(["task", "protocol", "seed"]).ngroups)
    for opt in ["robustness", "generalization", "sensitivity", "efficiency", "basemodel", "randfolds"]:
        p = RES / f"{opt}_results.csv"
        V[opt] = pd.read_csv(p) if p.exists() else None
    for t in ["table_iteration_v1_v2", "table_error_correlations", "table_worst_families_FCP", "table_point_accuracy",
              "table_basemodel", "table_randfolds"]:
        p = TAB / f"{t}.csv"
        V[t] = pd.read_csv(p) if p.exists() else None
    return V


TASK = {"mpea_hv": "MPEA hardness", "mpea_ys": "MPEA yield strength", "steel_ys": "Steel yield strength",
        "superhard_k": "Bulk modulus", "expt_hf": "Formation enthalpy", "supercon_tc": "Superconductor Tc"}


def fig_block(name, caption, width=6.3):
    p = FIG / f"{name}.png"
    w, h = Image.open(p).size
    import re
    alt = re.sub(r"\{+(fig|tab):\w+\}+\.?\s*", "", caption).replace("Fig. ", "").strip()[:150]
    return {"type": "figure", "path": str(p), "ratio": h / w, "width_in": width, "caption": runs(caption), "alt": alt}


# ------------------------------------------------------------------------------------------- results
def task_level_text(V):
    tl = V["st"]["tests"]["task_level_replication"]
    cm = V["cm"]; sh = cm[cm.protocol.isin(["system", "cluster"])]
    short = (0.9 - sh.pivot_table(index=["task", "protocol"], columns="method", values="coverage")).clip(lower=0).groupby(level=0).mean()
    isc = sh.groupby(["task", "method"]).interval_score_sd.mean().unstack()
    def wins(tab, m):
        return int((tab["FCP"] < tab[m]).sum())
    all6 = [m for m in ["SCP", "CV+", "CQR", "Ens-z", "GSCP"] if wins(short, m) == 6]
    claim(len(all6) == 5, "FCP smaller task-level shortfall than SCP, CV+, CQR, Ens-z, GSCP in all 6 tasks")
    w_wcp, w_gp = wins(short, "WCP"), wins(short, "GP")
    is6 = [m for m in ["SCP", "GP", "Ens-z", "GSCP"] if wins(isc, m) == 6]
    claim(len(is6) == 4, "task-level IS: FCP better in all 6 tasks vs SCP, GP, Ens-z, GSCP")
    p_cv, p_cqr = tl["interval_score FCP vs CV+"]["p"], tl["interval_score FCP vs CQR"]["p"]
    claim(p_cv > 0.05 and p_cqr > 0.05, "task-level IS vs CV+/CQR not significant")
    return ("Because the two shift protocols of a task share data, the comparison was repeated at the task level, with six fully "
            "independent units, each averaging its two shift protocols. FCP's shortfall was smaller than that of SCP, CV+, CQR, "
            "Ens-z and GSCP in all six tasks (exact Wilcoxon p = 0.031, the smallest attainable with six units). It was smaller "
            f"than WCP's in {w_wcp} and GP's in {w_gp} of six tasks (p = {tl['shortfall FCP vs WCP']['p']:.3f} and "
            f"{tl['shortfall FCP vs GP']['p']:.3f}). For the interval score, the task-level advantage was consistent against SCP, "
            f"GP, Ens-z and GSCP (six of six tasks), but not significant against CV+ (p = {p_cv:.3f}) or CQR (p = {p_cqr:.3f}). "
            "The coverage benefit is therefore robust at every level of analysis. The efficiency benefit over the best "
            "random-calibrated baselines is consistent in direction but limited by the number of independent datasets.")



def results(V):
    g, st = V["g"], V["st"]
    E = []
    pa = V["table_point_accuracy"]
    cm = V["cm"]
    r2 = cm[cm.method == "FCP"].pivot_table(index="task", columns="protocol", values="r2")
    drop_cl = (r2["random"] - r2["cluster"])
    claim((r2["cluster"] < r2["random"]).all(), "point accuracy (R2) is lower under cluster holdout than random for every task")
    E += [("h1", "7. Results"),
          ("h2", "7.1. Severity of the distribution shift"),
          ("p", "Holding out whole families degraded the shared point predictor in every task (Table {{tab:accuracy}}). Mean R² over tasks fell "
                f"from {r2['random'].mean():.3f} (random) to {r2['system'].mean():.3f} (unseen chemical system) and "
                f"{r2['cluster'].mean():.3f} (unseen composition cluster). The largest losses occurred for steel yield strength "
                f"(R² {r2.loc['steel_ys', 'random']:.2f} → {r2.loc['steel_ys', 'cluster']:.2f}) and superconductor Tc "
                f"({r2.loc['supercon_tc', 'random']:.2f} → {r2.loc['supercon_tc', 'cluster']:.2f}). The two protocols therefore "
                "represent moderate and severe extrapolation, respectively."),
          ("table2", None)]
    # RQ1
    h1 = st["tests"]["H1_random_calibration_undercovers_under_shift"]["results"]
    for m in ["SCP", "CV+", "CQR"]:
        claim(g("random", m) >= 0.895, f"{m} near nominal in random protocol")
        claim(g("system", m) < 0.88 and g("cluster", m) < 0.76, f"{m} under-covers under shift")
    claim(all(h1[m]["p"] < 0.05 for m in ["SCP", "CV+", "CQR", "WCP"]), "H1 significant for all four random-calibrated methods")
    E += [("h2", "7.2. RQ1: random-split calibration does not transfer to unseen families"),
          ("p", "In the random protocol, every conformal method attained its nominal 90% coverage (Fig. {{fig:coverage}}, left; Table {{tab:summary}}). "
                f"Mean coverage was {g('random', 'SCP'):.3f} for SCP, {g('random', 'CV+'):.3f} for CV+, {g('random', 'CQR'):.3f} "
                f"for CQR and {g('random', 'WCP'):.3f} for WCP. The same methods under-covered as soon as whole families were "
                f"held out: {g('system', 'SCP'):.3f}, {g('system', 'CV+'):.3f}, {g('system', 'CQR'):.3f} and "
                f"{g('system', 'WCP'):.3f} for unseen chemical systems, and {g('cluster', 'SCP'):.3f}, {g('cluster', 'CV+'):.3f}, "
                f"{g('cluster', 'CQR'):.3f} and {g('cluster', 'WCP'):.3f} for unseen composition clusters. The worst cell fell to "
                f"{V['summ'][(V['summ'].protocol == 'cluster') & (V['summ'].method == 'SCP')].min_cell_coverage.iloc[0]:.3f} (SCP). "
                "Over the 12 shift cells, the one-sided Wilcoxon test rejected nominal coverage for all four methods (H1: "
                f"p = {h1['SCP']['p']:.4f}, {h1['CV+']['p']:.4f}, {h1['CQR']['p']:.4f} and {h1['WCP']['p']:.4f}). Their median cell "
                f"coverages were {h1['SCP']['median']:.3f}, {h1['CV+']['median']:.3f}, {h1['CQR']['median']:.3f} and "
                f"{h1['WCP']['median']:.3f}, respectively."),
          ("p", "Density-ratio weighting (WCP) reduced the shortfall, but only by producing unbounded intervals: "
                f"{g('system', 'WCP', 'mean_inf_rate') * 100:.1f}% (system) and {g('cluster', 'WCP', 'mean_inf_rate') * 100:.1f}% "
                "(cluster) of its intervals were infinite. This happens because the classifier assigns the test alloys of a new family "
                "density ratios that dominate all calibration weights. Weighting cannot repair a support mismatch; it can only make "
                "it visible. Among the model-based intervals, the GP covered "
                f"{g('system', 'GP'):.3f} and {g('cluster', 'GP'):.3f}, and the base ensemble's own spread (Ens-z) covered only "
                f"{g('system', 'Ens-z'):.3f} and {g('cluster', 'Ens-z'):.3f}. Family-subsampled bagging thus does not by itself "
                "produce calibrated uncertainty. Random-forest tree spread (RF-z) is discussed in Section 7.4."),
          ("fig", ("fig3_coverage_by_protocol", "Fig. {{fig:coverage}}. Empirical coverage of 90% prediction intervals (α = 0.1) for ten "
                   "methods under the three protocols. Each marker is one dataset, averaged over 10 outer-split seeds. Horizontal "
                   "bars are means over datasets; the dashed line is the nominal level. Colour encodes the method group and marker "
                   "shape the individual method."))]
    # RQ2
    h2 = st["tests"]["H2_FCP_vs_baselines_coverage_shortfall"]["results"]
    h3 = st["tests"]["H3_FCP_vs_baselines_interval_score"]["results"]
    sig2 = [m for m in h2 if h2[m]["p_holm"] < 0.05 and h2[m]["median_diff"] < 0]
    claim(set(sig2) == {"SCP", "CV+", "CQR", "WCP", "GP", "Ens-z", "GSCP"}, "FCP shortfall significantly smaller than all baselines except RF-z")
    claim(h2["RF-z"]["p_holm"] > 0.05, "FCP vs RF-z shortfall not significant")
    sig3 = [m for m in h3 if np.isfinite(h3[m]["p_holm"]) and h3[m]["p_holm"] < 0.05 and h3[m]["median_diff"] < 0]
    claim(set(sig3) == {"SCP", "CV+", "CQR", "GP", "Ens-z", "GSCP"}, "FCP interval score significantly better than six baselines")
    claim(h3["RF-z"]["median_diff"] > 0 and h3["RF-z"]["p_holm"] > 0.05, "RF-z interval score lower than FCP but not significant")
    claim(g("system", "FCP") >= 0.9 and g("cluster", "FCP") >= 0.9, "FCP mean coverage >= 0.9 under both shifts")
    mins = V["summ"][(V["summ"].method == "FCP")].set_index("protocol").min_cell_coverage
    claim(sum(np.isclose(h2[m]["rank_biserial"], -1) for m in sig2) == 6, "rank-biserial = -1 for six baselines")
    E += [("h2", "7.3. RQ2: family-level calibration restores coverage"),
          ("p", f"FCP attained mean coverage {g('system', 'FCP'):.3f} on unseen chemical systems and {g('cluster', 'FCP'):.3f} on "
                f"unseen composition clusters. Its worst cells were {mins['system']:.3f} and {mins['cluster']:.3f}. In the random "
                f"protocol it was conservative ({g('random', 'FCP'):.3f}), as expected: calibrating on whole held-out families "
                "measures extrapolation error even when the test alloys are not extrapolations. FCP-W, which targets family-level "
                f"coverage, attained family coverage {g('system', 'FCP-W', 'mean_family_coverage'):.3f} under the system protocol, "
                f"against {g('system', 'FCP', 'mean_family_coverage'):.3f} for FCP and "
                f"{g('system', 'SCP', 'mean_family_coverage'):.3f} for SCP. Under the cluster protocol only eight training clusters "
                f"remain per outer fold, below the bound of Eq. (10), so {g('cluster', 'FCP-W', 'mean_inf_rate') * 100:.0f}% of its "
                "intervals were infinite by construction."),
          ("p", "Over the 12 shift cells, FCP's coverage shortfall max(0, 0.9 − coverage) was significantly smaller than that of "
                f"seven of the eight baselines after Holm correction (H2, Table {{tab:tests}}; p_Holm ≤ {max(h2[m]['p_holm'] for m in sig2):.3f}; "
                "rank-biserial r = −1 for six of them). The median paired reductions ranged from "
                f"{min(-h2[m]['median_diff'] for m in sig2) * 100:.1f} to {max(-h2[m]['median_diff'] for m in sig2) * 100:.1f} "
                "percentage points. Compared with the simplest family-calibrated alternative, GSCP, which holds out 25% of the "
                f"families for split calibration, the median reduction was small ({-h2['GSCP']['median_diff'] * 100:.1f} points) but "
                f"consistent (p_Holm = {h2['GSCP']['p_holm']:.3f}). Its effect was concentrated in the cluster protocol, where GSCP "
                f"covered only {g('cluster', 'GSCP'):.3f} because it calibrates on a few held-out clusters, whereas CV+ uses every "
                "training family once. The only baseline whose shortfall did not differ from FCP's was RF-z "
                f"(p_Holm = {h2['RF-z']['p_holm']:.2f})."),
          ("p", "Coverage alone can be bought with width. The interval score, which penalizes both width and misses, was "
                "significantly better (lower) for FCP than for SCP, CV+, CQR, GP, Ens-z and GSCP (H3; p_Holm ≤ "
                f"{max(h3[m]['p_holm'] for m in sig3):.3f}). WCP could not be scored because it returned infinite intervals in "
                f"{12 - h3['WCP']['n']} of the 12 cells. FCP's intervals were wider than those of the random-calibrated methods "
                f"(mean width {g('system', 'FCP', 'mean_width_sd'):.2f} vs {g('system', 'CV+', 'mean_width_sd'):.2f} SD(y) for CV+ "
                f"under the system protocol; {g('cluster', 'FCP', 'mean_width_sd'):.2f} vs {g('cluster', 'CV+', 'mean_width_sd'):.2f} "
                "under the cluster protocol; Fig. {{fig:tradeoff}}). The extra width is the price of covering extrapolation error that the narrower "
                "intervals miss: their miss penalties outweigh the width saving."),
          ("p", task_level_text(V)),
          ("fig", ("fig4_coverage_width_tradeoff", "Fig. {{fig:tradeoff}}. Coverage versus mean interval width (in units of SD(y)) under the "
                   "two shift protocols, averaged over datasets (α = 0.1). Methods above the dashed line meet the nominal level on "
                   "average; points further left are more efficient.")),
          ("table3", None), ("table4", None)]
    # RF-z discussion
    claim(g("random", "RF-z") > 0.94, "RF-z over-covers in-distribution")
    claim(V["cm"][(V["cm"].protocol == "random") & (V["cm"].method == "RF-z")].coverage.max() >= 0.98, "RF-z reaches 0.98 in a dataset")
    al = pd.read_csv(TAB / "table_alpha_sweep.csv")
    rfz80 = float(al[(al.protocol == "random") & (al.method == "RF-z") & (np.isclose(al.alpha, 0.2))].coverage.iloc[0])
    fcp80 = float(al[(al.protocol == "random") & (al.method == "FCP") & (np.isclose(al.alpha, 0.2))].coverage.iloc[0])
    E += [("h2", "7.4. A strong heuristic competitor: random-forest tree spread"),
          ("p", "RF-z deserves separate discussion. Its coverage was as high as FCP's under both shifts "
                f"({g('system', 'RF-z'):.3f} and {g('cluster', 'RF-z'):.3f}), and its interval score was lower on average, although "
                f"the difference was not significant (median paired difference {h3['RF-z']['median_diff']:+.3f} SD in favour of "
                f"RF-z, p_Holm = {h3['RF-z']['p_holm']:.3f}). RF-z is not calibrated, however. It over-covered in the random protocol "
                f"({g('random', 'RF-z'):.3f} at a nominal 0.90; {rfz80:.3f} at a nominal 0.80, against {fcp80:.3f} for FCP; "
                f"Supplementary Fig. {SFIG['alpha']}), and "
                "individual datasets reached 0.98. Its apparent robustness therefore comes from intervals that are systematically "
                "too wide in-distribution. That inflation happens to offset the extrapolation error under shift, but nothing "
                "guarantees it. It depends on forest hyper-parameters such as max_features and leaf size, and it cannot be dialled "
                "to a requested level. Section 9.4 asks the constructive question, whether family-level calibration of the forest's "
                "own tree spread combines its efficiency with calibrated coverage, and finds that it does.")]
    return E


def ablation(V):
    g = V["g"]; st = V["st"]["tests"]["H4_ablation"]["results"]
    claim(g("system", "GCV+") > g("system", "CV+") + 0.03 and g("cluster", "GCV+") > g("cluster", "CV+") + 0.1, "grouping drives coverage")
    claim(g("cluster", "GCV+[spread]", "mean_interval_score_sd") < g("cluster", "GCV+", "mean_interval_score_sd"), "spread improves IS cluster")
    claim(g("system", "GCV+[spread]", "mean_interval_score_sd") < g("system", "GCV+", "mean_interval_score_sd"), "spread improves IS system")
    claim(g("cluster", "GCV+[novelty]", "mean_interval_score_sd") > g("cluster", "GCV+", "mean_interval_score_sd"), "novelty worsens IS cluster")
    claim(g("cluster", "FCP", "mean_cov_high_novelty") > g("cluster", "GCV+", "mean_cov_high_novelty") + 0.03, "novelty raises high-novelty coverage")
    claim(g("system", "NCV+") < 0.89 and g("cluster", "NCV+") < 0.87, "normalisation without grouping under-covers")
    it = V["table_iteration_v1_v2"]
    fcl = it[(it.method == "FCP") & (it.protocol == "cluster")].iloc[0]
    return [("h1", "8. Ablation study"),
            ("p", "Table {{tab:ablation}} and Fig. {{fig:ablation}} decompose FCP into its three design choices: family-grouped folds, the scale model (none, "
                  "spread only, novelty only, both) and family weights. **Grouping is the decisive component.** Switching CV+ from "
                  "random to family-grouped folds, with nothing else changed, raised mean coverage from "
                  f"{g('system', 'CV+'):.3f} to {g('system', 'GCV+'):.3f} (system) and from {g('cluster', 'CV+'):.3f} to "
                  f"{g('cluster', 'GCV+'):.3f} (cluster). Over the 12 shift cells the median gain was "
                  f"{st['GCV+_vs_CV+_coverage']['median_diff'] * 100:.1f} percentage points (Wilcoxon p = "
                  f"{st['GCV+_vs_CV+_coverage']['p']:.4f}). Normalization *without* grouping (NCV+, analogous to the normalized "
                  "conformal method used for steels with random splits [@boruah2026]) narrowed the intervals but did not fix "
                  f"coverage ({g('system', 'NCV+'):.3f} and {g('cluster', 'NCV+'):.3f}). FCP covered more than NCV+ in the paired "
                  f"comparison (median +{st['FCP_vs_NCV+_coverage']['median_diff'] * 100:.1f} points, p = "
                  f"{st['FCP_vs_NCV+_coverage']['p']:.3f})."),
            ("p", "The two difficulty signals play different roles. The ensemble spread improved efficiency: the interval score "
                  f"of GCV+[spread] was {g('system', 'GCV+[spread]', 'mean_interval_score_sd'):.3f} vs "
                  f"{g('system', 'GCV+', 'mean_interval_score_sd'):.3f} (system) and {g('cluster', 'GCV+[spread]', 'mean_interval_score_sd'):.3f} "
                  f"vs {g('cluster', 'GCV+', 'mean_interval_score_sd'):.3f} (cluster) for the unnormalized grouped CV+. Compositional "
                  "novelty instead improved coverage for the most novel alloys. In the highest novelty tertile under cluster "
                  f"holdout, coverage was {g('cluster', 'FCP', 'mean_cov_high_novelty'):.3f} for FCP against "
                  f"{g('cluster', 'GCV+', 'mean_cov_high_novelty'):.3f} for GCV+ (12-cell median difference "
                  f"+{st['FCP_vs_GCV+_cov_novelty_high']['median_diff'] * 100:.1f} points, p = "
                  f"{st['FCP_vs_GCV+_cov_novelty_high']['p']:.4f}; Fig. {{fig:novelty}}). Novelty also widened the intervals, so that under the "
                  f"cluster protocol FCP's interval score ({g('cluster', 'FCP', 'mean_interval_score_sd'):.3f}) was worse than "
                  f"spread-only normalization ({g('cluster', 'GCV+[spread]', 'mean_interval_score_sd'):.3f}). Over the 12 cells, "
                  f"the FCP vs GCV+ interval-score difference was not significant (p = {st['FCP_vs_GCV+_interval_score_sd']['p']:.2f}). "
                  "Hence the pre-specified 'both' scale buys more uniform coverage across novelty levels at a modest efficiency "
                  "cost. A user who values average efficiency over conditional coverage should prefer the spread-only scale."),
            ("p", "Family weights (the -W variants) raised family-level coverage "
                  f"(FCP-W vs FCP: median +{st['FCP-W_vs_FCP_family_coverage']['median_diff'] * 100:.1f} points, p = "
                  f"{st['FCP-W_vs_FCP_family_coverage']['p']:.4f}) at the cost of wider intervals. They also became unbounded "
                  "when fewer than nine training families were available, as Eq. (10) predicts."),
            ("p", "**Revision history of the scale model.** The first version of the scale model (v1) extrapolated the log-linear "
                  "fit beyond the range of the difficulty signals seen during fitting. It produced a few extremely wide intervals "
                  "for test alloys with rare processing categories or compositions. Clamping the signals to their fitting range "
                  "(v2, used throughout) left coverage unchanged (FCP, alloy tasks, cluster protocol: "
                  f"{fcl.coverage_v1:.3f} vs {fcl.coverage_v2:.3f}) and left the median width unchanged "
                  f"({fcl.median_width_sd_v1:.2f} vs {fcl.median_width_sd_v2:.2f} SD). It reduced the mean width from "
                  f"{fcl.mean_width_sd_v1:.2f} to {fcl.mean_width_sd_v2:.2f} SD and the interval score from "
                  f"{fcl.interval_score_v1:.2f} to {fcl.interval_score_v2:.2f} (Supplementary Table S1). The change was made after "
                  "the interim analysis, and it is documented together with the original results."),
            ("table5", None),
            ("fig", ("fig6_ablation", "Fig. {{fig:ablation}}. Ablation of FCP under the two shift protocols: mean coverage (left) and interval "
                     "score (right) over datasets. GCV+: family-grouped CV+ without normalization; [spread] / [novelty]: scale model "
                     "with one signal; -W: family weights; NCV+: normalization with random folds.")),
            ("fig", ("fig5_conditional_coverage_novelty", "Fig. {{fig:novelty}}. Coverage within tertiles of test-alloy novelty (k-nearest-"
                     "neighbour distance to the training alloys), averaged over datasets."))]


def error_analysis(V):
    ec = V["table_error_correlations"]
    f = ec[(ec.method == "FCP") & (ec.variable == "z")]
    s = ec[(ec.method == "SCP") & (ec.variable == "z")]
    neg = f[(f.spearman_rho < 0) & (f.p < 0.05)]
    claim(len(neg) >= 4, "target extremity negatively associated with family coverage in >= 4 tasks for FCP")
    wf = V["table_worst_families_FCP"]
    fe = pd.read_csv(TAB / "family_level_errors.csv")
    sub = fe[(fe.method.isin(["SCP", "FCP"])) & (fe.n >= 5)]
    q = pd.Series({m: d[d.z >= d.z.quantile(5 / 6)]["cov"].mean() for m, d in sub.groupby("method")})
    claim(q["FCP"] > q["SCP"] + 0.1, "FCP improves coverage for extreme-property families relative to SCP")
    claim(q["FCP"] < 0.88, "extreme-property families remain under-covered by FCP")
    ys = wf[wf.task == "mpea_ys"]
    return [("h1", "11. Error analysis"),
            ("p", "To see where intervals still fail, coverage was computed for every test family with at least five alloys in the "
                  "system protocol (all seeds pooled; Fig. {{fig:errors}}). The dominant failure mode was **property extremity**, not "
                  "compositional novelty. For FCP, within-family coverage decreased with the family's mean distance from the median "
                  f"target (|y − median|/IQR) in {len(neg)} of 6 tasks (Spearman ρ from {f.spearman_rho.min():.2f} to "
                  f"{f.spearman_rho.max():.2f}). The families in the most extreme sextile were covered {q['FCP']:.2f} of the time by "
                  f"FCP, against {q['SCP']:.2f} by SCP. FCP therefore reduced this failure substantially but did not remove it. The "
                  "association with novelty was weaker and of inconsistent sign, which suggests that, once calibration is family-level, "
                  "the remaining misses are dominated by regression toward the mean of the training labels for families with "
                  f"unusually high or low properties. Supplementary Fig. {SFIG['parity']} illustrates this for MPEA hardness: the uncovered "
                  "alloys concentrate above about 800 HV."),
            ("p", "The families with the lowest FCP coverage are listed in the Supplementary Material. Several are metallurgically distinctive within their "
                  "datasets. Examples in the MPEA yield-strength data are the Cr–Fe–Ni–Ti and Al–Co–Cr–Fe–Mo–Ni systems and the "
                  "refractory Nb–Ta–Ti and Al–Mo–Nb–Ta–Ti–Zr systems. The ensemble predicted their strength levels poorly: the mean "
                  f"absolute error of the worst family exceeded {ys.abserr.max():.0f} MPa. An Fe–As–O–Sm (iron-pnictide) family "
                  "appears among the superconductors, and maraging-type Co–Fe–Mo–Ni–Ti steels among the steels. These are cases in which "
                  "a new strengthening or pairing mechanism, absent from the training families, governs the property. No "
                  "calibration of residuals can anticipate such a mechanism. FCP's intervals are honest about the *average* "
                  "extrapolation error over families, not about every individual family."),
            ("fig", ("fig9_error_analysis_families", "Fig. {{fig:errors}}. Within-family coverage (system holdout, families with ≥ 5 alloys, "
                     "all tasks and seeds pooled) against the family's mean target extremity (left) and mean novelty (right), in "
                     "sextiles.")),
            ]


# ------------------------------------------------------------------------------------------- tables
SRC = {"mpea_hv": "Borg et al. [@borg2020]", "mpea_ys": "Borg et al. [@borg2020]", "steel_ys": "Matbench [@dunn2020]",
       "superhard_k": "Mansouri Tehrani et al. [@tehrani2018]", "expt_hf": "Kingsbury et al. [@kingsbury2022]",
       "supercon_tc": "Hamidieh [@hamidieh2018]"}
UNIT = {"mpea_hv": "HV", "mpea_ys": "MPa", "steel_ys": "MPa", "superhard_k": "GPa", "expt_hf": "eV/atom", "supercon_tc": "K"}


def num(x):
    """Plain (non-scientific) formatting with ~3 significant figures."""
    ax = abs(x)
    if ax >= 100:
        return f"{x:.0f}"
    if ax >= 10:
        return f"{x:.1f}"
    if ax >= 1:
        return f"{x:.2f}"
    return f"{x:.3f}"


def tables(V, bib):
    T = {}
    ds = V["ds"].set_index("task")
    rows = []
    for t in TASK:
        r = ds.loc[t]
        rows.append([TASK[t], UNIT[t], SRC[t], str(int(r.n)), str(int(r.n_features)), str(int(r.n_systems)),
                     f"{num(r.y_mean)} ± {num(r.y_sd)}", f"{num(r.y_min)} to {num(r.y_max)}"])
    T["table1"] = {"type": "table", "caption": runs("**Table {{tab:datasets}}.** Datasets after cleaning (identical inputs merged by median). "
                   "Systems: number of F1 alloy families (elements ≥ 1 at.%); every task also has 10 F2 composition clusters."),
                   "header": ["Task", "Unit", "Source", "n", "Features", "Systems", "Mean ± SD", "Range"],
                   "rows": rows, "col_widths": [0.19, 0.08, 0.17, 0.07, 0.09, 0.09, 0.15, 0.16]}
    pa = V["table_point_accuracy"]
    T["table2"] = {"type": "table", "caption": runs("**Table {{tab:accuracy}}.** R² of the shared point predictor (family-bagged LightGBM ensemble fitted on the "
                   "whole outer training part) on the outer test folds, mean ± SD over 10 seeds."),
                   "header": ["Task", "Random", "Unseen system", "Unseen cluster"],
                   "rows": [[r.Task, r["R² random"], r["R² system"], r["R² cluster"]] for _, r in pa.iterrows()],
                   "col_widths": [0.34, 0.22, 0.22, 0.22]}
    summ = V["summ"]
    KEY = ["SCP", "CV+", "CQR", "WCP", "GP", "RF-z", "Ens-z", "GSCP", "FCP", "FCP-W"]
    rows = []
    for m in KEY:
        r = [m]
        for p in ["random", "system", "cluster"]:
            x = summ[(summ.protocol == p) & (summ.method == m)].iloc[0]
            r += [f"{x.mean_coverage:.3f}", f"{x.min_cell_coverage:.3f}",
                  f"{x.mean_width_sd:.2f}" + ("*" if x.mean_inf_rate > 0 else ""),
                  f2(x.mean_interval_score_sd)]
        rows.append(r)
    T["table3"] = {"type": "table", "font_size": 14,
                   "caption": runs("**Table {{tab:summary}}.** Summary over the six datasets (α = 0.1; 10 seeds per dataset). Cov: mean coverage; "
                                   "Min: worst dataset; W: mean finite interval width / SD(y); IS: mean interval score / SD(y). "
                                   "*Some intervals infinite (WCP: density-ratio weights; FCP-W: fewer than 9 training families)."),
                   "header": ["Method", "Cov", "Min", "W", "IS", "Cov", "Min", "W", "IS", "Cov", "Min", "W", "IS"],
                   "rows": [["", "Random", "", "", "", "Unseen system", "", "", "", "Unseen cluster", "", "", ""]] + rows,
                   "col_widths": [0.10] + [0.075] * 12}
    h2 = V["st"]["tests"]["H2_FCP_vs_baselines_coverage_shortfall"]["results"]
    h3 = V["st"]["tests"]["H3_FCP_vs_baselines_interval_score"]["results"]
    rows = []
    for m in ["SCP", "CV+", "CQR", "WCP", "GP", "RF-z", "Ens-z", "GSCP"]:
        a, b = h2[m], h3[m]
        def fmt(r, k):
            return "n/a" if not np.isfinite(r.get(k, np.nan)) else (f"{r[k]:.4f}" if k.startswith("p") else f"{r[k]:+.3f}")
        rows.append([f"FCP vs {m}", str(a.get("n_eff", "")), fmt(a, "median_diff"), f"[{a['ci_lo']:+.3f}, {a['ci_hi']:+.3f}]", f"{a['rank_biserial']:+.2f}",
                     fmt(a, "p_holm"), fmt(b, "median_diff") if b["n"] >= 3 else "n/a (∞)",
                     f"[{b['ci_lo']:+.3f}, {b['ci_hi']:+.3f}]" if b["n"] >= 3 else "–",
                     f"{b['rank_biserial']:+.2f}" if b["n"] >= 3 else "–", fmt(b, "p_holm") if b["n"] >= 3 else "–"])
    T["table4"] = {"type": "table", "font_size": 15,
                   "caption": runs("**Table {{tab:tests}}.** Paired comparisons over the 12 shift cells (6 tasks × 2 shift protocols; Wilcoxon "
                                   "signed-rank, Holm-corrected over 8 baselines). Δ: median paired difference (FCP − baseline) with "
                                   "bootstrap 95% CI; r: matched-pairs rank-biserial correlation. Negative Δ favours FCP. n_eff: cells with a non-zero "
                                   "shortfall difference (the signed-rank test ignores ties). For RF-z the shortfall is zero in most "
                                   "cells for both methods, so Δ and its CI are 0."),
                   "header": ["Comparison", "n_eff", "Δ shortfall", "95% CI", "r", "p_Holm", "Δ IS", "95% CI", "r", "p_Holm"],
                   "rows": rows, "col_widths": [0.14, 0.06, 0.1, 0.14, 0.06, 0.08, 0.1, 0.14, 0.06, 0.08]}
    ab = pd.read_csv(TAB / "table_ablation.csv")
    order = ["CV+", "NCV+", "GCV+", "GCV+[spread]", "GCV+[novelty]", "FCP", "GCV+-W", "FCP-W"]
    desc = {"CV+": ("random", "–", "1"), "NCV+": ("random", "spread+novelty", "1"), "GCV+": ("family", "–", "1"),
            "GCV+[spread]": ("family", "spread", "1"), "GCV+[novelty]": ("family", "novelty", "1"),
            "FCP": ("family", "spread+novelty", "1"), "GCV+-W": ("family", "–", "1/n_g"), "FCP-W": ("family", "spread+novelty", "1/n_g")}
    rows = []
    for m in order:
        r = [m, *desc[m]]
        for p in ["system", "cluster"]:
            x = ab[(ab.protocol == p) & (ab.method == m)].iloc[0]
            r += [f"{x.mean_coverage:.3f}", f2(x.mean_interval_score_sd), f"{x.mean_cov_high_novelty:.3f}"]
        rows.append(r)
    T["table5"] = {"type": "table", "font_size": 15,
                   "caption": runs("**Table {{tab:ablation}}.** Ablation (α = 0.1, mean over datasets). Cov: coverage; IS: interval score / SD(y); "
                                   "Cov_{hi}: coverage in the highest novelty tertile."),
                   "header": ["Variant", "Folds", "Scale", "Weights", "Cov", "IS", "Cov_hi", "Cov", "IS", "Cov_hi"],
                   "rows": [["", "", "", "", "Unseen system", "", "", "Unseen cluster", "", ""]] + rows,
                   "col_widths": [0.13, 0.08, 0.15, 0.08, 0.09, 0.09, 0.09, 0.1, 0.09, 0.1]}
    wf = V["table_worst_families_FCP"].head(10)
    T["table7"] = {"type": "table", "font_size": 16,
                   "caption": runs("**Table {{tab:worst}}.** Families with the lowest FCP coverage under system holdout (≥ 5 alloys; means over "
                                   "seeds). Extremity: mean |y − median|/IQR; MAE in target units."),
                   "header": ["Task", "Family (chemical system)", "Coverage", "Alloys", "Novelty", "Extremity", "MAE"],
                   "rows": [[TASK[r.task], r.fam, f"{r['cov']:.2f}", f"{r.n:.0f}", f"{r.nov:.2f}", f"{r.z:.2f}", f"{r.abserr:.3g}"]
                            for _, r in wf.iterrows()],
                   "col_widths": [0.2, 0.24, 0.11, 0.09, 0.11, 0.12, 0.13]}
    return T


# ------------------------------------------------------------------------------------------- discussion etc.
def discussion(V):
    g = V["g"]
    return [("h1", "12. Discussion"),
            ("p", "**What the results mean for alloy design.** A materials-informatics workflow that reports 'conformal' 90% "
                  "intervals calibrated on random held-out alloys delivered, on average, "
                  f"{rc_range(V, 'system')} coverage on new chemical systems and "
                  f"{rc_range(V, 'cluster')} on new regions of composition space (the upper ends belong to WCP, which "
                  "reached them only by returning infinite intervals for part of the alloys). In the worst "
                  "datasets coverage was close to two-thirds. The nominal level is therefore not a property of the method alone. "
                  "It is a property of the method *and* of how the calibration data relate to the deployment data. The remedy "
                  "studied here is simple to state: calibrate on whole held-out families, so that the calibration residuals "
                  "measure the kind of error the model will make in use. With that change, coverage on unseen families returned "
                  "to the nominal level on average. The price is intervals about "
                  f"{(g('system', 'FCP', 'mean_width_sd') / g('system', 'CV+', 'mean_width_sd') - 1) * 100:.0f}% (system) and "
                  f"{(g('cluster', 'FCP', 'mean_width_sd') / g('cluster', 'CV+', 'mean_width_sd') - 1) * 100:.0f}% (cluster) wider "
                  "than the under-covering random-calibrated ones. Measured by the interval score, which accounts for both width "
                  "and misses, FCP was better than every baseline except random-forest tree spread at the level of the 12 "
                  "dataset-protocol cells. At the level of the six independent datasets, the advantage over CV+ and CQR was "
                  "consistent in direction but not statistically significant."),
            ("p", "**Choosing the family definition.** The family is the unit of novelty against which coverage is certified. "
                  "Chemical systems are natural for HEA/MPEA design campaigns that open new element combinations. Composition "
                  "clusters are natural when moving to distant regions of an existing system. Section 9.2 shows that calibrating on "
                  "a finer definition than the actual shift costs coverage. Section 9.3 shows that FCP cannot correct shifts that "
                  "are not family novelty at all, such as new processing routes. Practitioners should calibrate at the "
                  "level of novelty they intend to explore. With few families, they should prefer unweighted FCP, whose interval "
                  "stays finite, over FCP-W, whose interval correctly becomes unbounded."),
            ("p", "**Relation to prior work.** The coverage collapse reported for polymer chemistry holdouts [@han2026;@akdogan2026] "
                  "is reproduced here for alloys and inorganic compounds, across six datasets and two kinds of family shift. "
                  "Normalized scores, which restore label-conditional coverage under random splits in steels [@boruah2026], do not "
                  "restore coverage under family shift unless the calibration folds are grouped (NCV+ vs FCP, Section 8). "
                  "Recalibration with labelled data from the new domain [@morger2021;@morger2022] is effective when such data "
                  "exist; FCP is the corresponding remedy *before* any alloy of the new family has been measured. "
                  "Density-ratio weighting [@tibshirani2019] is unsuitable when the test family lies outside the support of the "
                  "calibration data, as is typical of alloy discovery. The family-level construction follows the hierarchical view "
                  "of Dunn et al. [@dunn2023], adapted to cross-fitting, normalized scores and a leakage-free scale model."),
            ("p", "**Is the extra cost worth it?** FCP costs about as much as CV+ and a few times as much as split conformal "
                  "prediction (Section 10). The cheapest family-calibrated alternative, GSCP, came close to FCP when many families "
                  f"were available (unseen systems: {g('system', 'GSCP'):.3f} vs {g('system', 'FCP'):.3f}). It failed when only a "
                  f"few families existed (unseen clusters: {g('cluster', 'GSCP'):.3f} vs {g('cluster', 'FCP'):.3f}), because a single "
                  "calibration split then contains only one or two families. Because FCP uses every family once for calibration, "
                  "its benefit grows as the number of families shrinks, which is exactly the situation of a new alloy class with "
                  "few explored systems. For databases with hundreds of families and tight compute budgets, GSCP is a defensible "
                  "and cheaper choice."),
            ("p", "**Practical recommendation.** For screening alloys from unexplored families, (i) define families from "
                  "composition before modelling; (ii) calibrate with family-grouped folds (FCP; with random-forest models, normalized by "
                  "the forest's tree spread, FCP-RFσ), or with a family-held-out calibration split (GSCP) when many families and "
                  "little compute are available; (iii) report the coverage obtained under a family-holdout "
                  "evaluation, not under random cross-validation; and (iv) treat alloys with predicted properties far outside the "
                  "training range, and alloys in the VEC transition band between BCC- and FCC-stable compositions, with extra caution, "
                  "because that is where the remaining misses concentrate (Sections 7.6 and 11)."),
            ]


DUPS = 0


def confirm_stats():
    p = RES / "statistics_confirm.json"
    return json.load(open(p)) if p.exists() else None


CTASK = {"mpea_uts": "MPEA ultimate tensile strength [@borg2020]", "mpea_elong": "MPEA tensile elongation [@borg2020]",
         "steel_uts": "steel tensile strength (Citrine steel data distributed with matminer [@ward2018])",
         "superhard_g": "shear modulus [@tehrani2018]", "expt_gap": "experimental band gap [@zhuo2018]"}


def confirm_section(V):
    c = confirm_stats()
    if c is None:
        return []
    sm = pd.read_csv(TAB / "table_confirm_summary.csv").set_index(["protocol", "method"])
    q = lambda p, m, k="mean_coverage": float(sm.loc[(p, m), k])
    ok = c["criteria_met"]
    yn = lambda b: "met" if b else "not met"
    c5 = c["C5"]; c6 = c["C6"]
    txt = ("To test whether the conclusions, and the post hoc FCP-RFσ, hold beyond the data that shaped them, a confirmatory "
           "study was pre-registered (hypotheses, success criteria and a promotion rule committed to the repository before any "
           "run; Supplementary Material) on five tasks never used in the exploratory work: "
           + ", ".join(CTASK[t] for t in c["tasks"]) + ". Four of them are new properties of alloys or compounds already "
           "present in Section 7; the band-gap set is an independent material class. The configuration was unchanged (10 seeds, "
           f"three protocols; {c['n_cells']} new shift cells). "
           f"C1 (random-calibrated methods under-cover; one-sided Wilcoxon) was {yn(ok['C1'])}: SCP covered {q('system', 'SCP'):.3f} "
           f"and {q('cluster', 'SCP'):.3f} (p = {c['C1']['SCP']['p']:.4f}), CV+ {q('system', 'CV+'):.3f} and {q('cluster', 'CV+'):.3f} "
           f"(p = {c['C1']['CV+']['p']:.4f}), CQR {q('system', 'CQR'):.3f} and {q('cluster', 'CQR'):.3f} (p = {c['C1']['CQR']['p']:.4f}). "
           f"C2 (smaller shortfall for FCP than SCP, CV+, CQR and GSCP; Holm) was {yn(ok['C2'])} (p_Holm "
           + ", ".join(f"{m} {c['C2'][m]['p_holm']:.4f}" for m in c["C2"]) + "). "
           f"C3 (FCP ≥ 0.88 under both shifts) was {yn(ok['C3'])}: {c['C3']['system']:.3f} and {c['C3']['cluster']:.3f}. "
           f"For FCP-RFσ, C4 (coverage ≥ 0.88) was {yn(ok['C4'])} ({c['C4']['system']:.3f} and {c['C4']['cluster']:.3f}), "
           f"C5 (lower interval score than FCP) was {yn(ok['C5'])} (median paired difference {c5['median_diff']:+.3f} SD, "
           f"p = {c5['p']:.4f}), and C6 (better in-distribution calibration than RF-z) was {yn(ok['C6'])} "
           f"({c6['alpha=0.1']['FCP-RFsigma']:.3f} vs {c6['alpha=0.1']['RF-z']:.3f} at nominal 0.90; "
           f"{c6['alpha=0.2']['FCP-RFsigma']:.3f} vs {c6['alpha=0.2']['RF-z']:.3f} at 0.80). ")
    if c["promoted"]:
        txt += ("By the pre-registered rule, FCP-RFσ is therefore promoted from a post hoc observation to the recommended "
                "variant for random-forest models.")
    else:
        txt += ("By the pre-registered rule, FCP-RFσ therefore remains a post hoc observation; the criteria it failed are "
                "reported above.")
    E = [("h2", "9.5. Pre-registered confirmatory study"), ("p", txt), ("table_confirm", None)]
    rows = []
    for m in ["SCP", "CV+", "CQR", "WCP", "GP", "RF-z", "GSCP", "MCP", "FCP", "FCP-W", "FCP-RFsigma"]:
        r = [m.replace("RFsigma", "RFσ")]
        for p in ["random", "system", "cluster"]:
            if (p, m) in sm.index:
                r += [f"{q(p, m):.3f}", f"{q(p, m, 'min_cell'):.3f}", f2(q(p, m, 'mean_interval_score_sd'))]
            else:
                r += ["", "", ""]
        rows.append(r)
    TB["table_confirm"] = {"type": "table", "font_size": 14,
        "caption": runs("**Table {{tab:confirm}}.** Pre-registered confirmatory study on five new tasks (α = 0.1, 10 seeds). "
                        "Cov: mean coverage over tasks; Min: worst task; IS: mean interval score / SD(y)."),
        "header": ["Method", "Cov", "Min", "IS", "Cov", "Min", "IS", "Cov", "Min", "IS"],
        "rows": [["", "Random", "", "", "Unseen system", "", "", "Unseen cluster", "", ""]] + rows,
        "col_widths": [0.13] + [0.0966] * 9}
    return E


def metallurgy_section(V):
    t = pd.read_csv(TAB / "table_metallurgy.csv")
    t = t[t.protocol == "system"]
    q = lambda task, dim, g, m: float(t[(t.task == task) & (t.dimension == dim) & (t.group == g) & (t.method == m)].coverage.iloc[0])
    w = lambda task, dim, g: float(t[(t.task == task) & (t.dimension == dim) & (t.group == g) & (t.method == "FCP")].width_sd.iloc[0])
    mid, bcc, fcc = "6.87-8 (mixed)", "VEC<6.87 (BCC-favoured)", "VEC>=8 (FCC-favoured)"
    claim(q("mpea_ys", "vec_regime", mid, "SCP") < min(q("mpea_ys", "vec_regime", bcc, "SCP"), q("mpea_ys", "vec_regime", fcc, "SCP")),
          "YS: SCP worst in the mixed-VEC band")
    claim(q("mpea_hv", "vec_regime", mid, "SCP") < min(q("mpea_hv", "vec_regime", bcc, "SCP"), q("mpea_hv", "vec_regime", fcc, "SCP")),
          "HV: SCP worst in the mixed-VEC band")
    claim(q("mpea_ys", "vec_regime", mid, "FCP") > q("mpea_ys", "vec_regime", mid, "SCP") + 0.08, "FCP improves mixed-VEC YS by > 8 points")
    claim(q("mpea_ys", "vec_regime", mid, "FCP") < 0.9, "FCP still below nominal in mixed-VEC YS")
    claim(q("mpea_ys", "alloy_class", "refractory", "SCP") > q("mpea_ys", "alloy_class", "3d-transition", "SCP"), "refractory easier than 3d (YS, SCP)")
    claim(q("mpea_ys", "phase", "other", "SCP") < min(q("mpea_ys", "phase", "BCC", "SCP"), q("mpea_ys", "phase", "FCC", "SCP")), "multiphase hardest (YS, SCP)")
    ws = [w("mpea_ys", "vec_regime", g) for g in [mid, bcc, fcc]]
    return [("h2", "7.6. Metallurgical interpretation"),
            ("p", "Where do random-split intervals fail, metallurgically? For the MPEA tasks, coverage under unseen-chemical-system "
                  "holdout was broken down by alloy class, reported phase, valence-electron concentration (VEC) and atomic-size "
                  "mismatch δ [@zhang2008] (Fig. {{fig:metallurgy}}; Supplementary Material). The failures were concentrated where the "
                  "composition–property relation is least smooth. In the VEC band 6.87–8, between the empirical BCC- and "
                  "FCC-stability limits of high-entropy alloys [@guo2011;@miracle2017], SCP covered only "
                  f"{q('mpea_ys', 'vec_regime', mid, 'SCP'):.2f} (yield strength) and {q('mpea_hv', 'vec_regime', mid, 'SCP'):.2f} "
                  f"(hardness), against {q('mpea_ys', 'vec_regime', bcc, 'SCP'):.2f} and {q('mpea_ys', 'vec_regime', fcc, 'SCP'):.2f} for "
                  "BCC- and FCC-favoured yield-strength alloys. Alloys reported as multiphase were the hardest phase class "
                  f"(SCP {q('mpea_ys', 'phase', 'other', 'SCP'):.2f}), and 3d-transition-metal alloys were harder than refractory ones "
                  f"(SCP {q('mpea_ys', 'alloy_class', '3d-transition', 'SCP'):.2f} vs {q('mpea_ys', 'alloy_class', 'refractory', 'SCP'):.2f}). "
                  "This is the regime of Al- or Ti-alloyed CoCrFeNi-type systems, where small composition changes move the alloy "
                  "from FCC through FCC + BCC to BCC and the strength changes abruptly [@wang2012]; a new system in this band is "
                  "extrapolation across a phase boundary that random calibration alloys rarely represent. FCP raised coverage "
                  f"in the transition band to {q('mpea_ys', 'vec_regime', mid, 'FCP'):.2f} and "
                  f"{q('mpea_hv', 'vec_regime', mid, 'FCP'):.2f} (FCP-RFσ {q('mpea_ys', 'vec_regime', mid, 'FCP-RFsigma'):.2f} and "
                  f"{q('mpea_hv', 'vec_regime', mid, 'FCP-RFsigma'):.2f}), but its yield-strength intervals there were hardly wider "
                  f"than elsewhere ({ws[0]:.2f} vs {ws[1]:.2f} and {ws[2]:.2f} SD), because neither of its difficulty signals "
                  "encodes proximity to a phase boundary. A physically informed difficulty signal, such as the distance of VEC from "
                  "the transition band, is a natural extension that should be tested prospectively rather than tuned here."),
            ("fig", ("fig13_metallurgy", "Fig. {{fig:metallurgy}}. Coverage of 90% intervals for MPEA alloys from unseen chemical "
                     "systems by alloy class (3d-transition, mixed, refractory) and VEC regime (< 6.87 BCC-favoured, 6.87–8 "
                     "transition, ≥ 8 FCC-favoured); means over 10 seeds (FCP-RFσ: 5 seeds)."))]


def CONFIRM_LIMIT(V):
    c = confirm_stats()
    if c is None:
        return "it should be confirmed on independent data before it is relied upon."
    if c["promoted"]:
        return ("its pre-registered confirmation (Section 9.5) used new properties of partly the same alloys plus one "
                "independent material set, so confirmation on further independent alloy data remains desirable.")
    return "its pre-registered confirmation (Section 9.5) did not meet all criteria, so it remains a post hoc observation."


def limitations(V):
    global DUPS
    a = pd.read_csv(TAB / "table_duplicate_spelling_audit.csv").set_index("task")
    DUPS = int(a.loc["supercon_tc", "rows_with_alt_spelling"])
    ex = a.loc["supercon_tc"]
    claim(max(abs(ex[f"{m}_random_cov_all"] - ex[f"{m}_random_cov_excl"]) for m in ["SCP", "CV+", "FCP"]) <= 0.005,
          "duplicate spellings change random coverage by <= 0.005")
    claim(int(a.drop("supercon_tc").rows_with_alt_spelling.sum()) == 0, "no duplicate spellings outside supercon")
    return [("h1", "13. Limitations"),
            ("bullets", [
                "No new finite-sample theorem is proved for the full normalized, family-weighted CV+ construction. Validity on new "
                "families is assessed empirically on six datasets, and it rests on the families being approximately exchangeable "
                "units. A design campaign that deliberately moves *away* from all known families (adaptive or feedback shift "
                "[@fannjiang2022]) violates this assumption.",
                "Coverage is marginal over alloys (FCP) or over families (FCP-W), not conditional on an individual alloy. Families "
                "with extreme properties remained under-covered (Section 11).",
                "Under the cluster protocol only ten families exist per dataset. Family-level (FCP-W) statements at α = 0.1 are "
                "then impossible (Eq. 10), and the outer partition of the balanced protocol is identical across seeds (Section 9.6).",
                "All datasets are public compilations. MPEA entries from different publications differ in processing and testing "
                "details that are only partly encoded, and inter-laboratory bias cannot be separated from model error.",
                "Features are composition-based (plus processing and test conditions for MPEA). Microstructure, defect and "
                "thermomechanical-history descriptors, which govern many mechanical properties, were not available.",
                "Superconductor data were subsampled to about 4,000 compounds by whole chemical systems to fit the computational "
                "budget (4 CPU cores). Results for the full set may differ quantitatively.",
                "Energy consumption was not measured. All runs used CPUs only, and per-fold costs are reported as wall time. "
                "Interval formation scales as O(*n* log *n*) per test alloy, which was negligible here but would call for an "
                "approximation (e.g. a pooled quantile of normalized scores) for databases with 10^{5} or more alloys.",
                "No prospective validation was performed: no new alloy was synthesized and tested. The chronological test "
                "(Section 9.3) is the closest available proxy.",
                f"FCP-RFσ was formulated after the main results (Section 9.4); {CONFIRM_LIMIT(V)} The alloy-family threshold (1 at.%) and the number of composition clusters (10) were fixed "
                "and not varied.",
                f"In the superconductor data, {DUPS} compositions appear under more than one formula spelling. They cannot cross "
                "folds in the family-holdout protocols, but can in the random protocol; excluding them changed random-protocol "
                "coverage by at most 0.004 (code/scripts/audit_duplicate_spellings.py).",
                "Hyper-parameters were fixed defaults and were not tuned per dataset. Tuning would raise point accuracy for every "
                "method alike and is unlikely to change the calibration comparison, but this was not tested.",
            ])]


def conclusion(V):
    g = V["g"]
    return [("h1", "14. Conclusions"),
            ("p", "Prediction intervals for machine-learned alloy properties were examined in the setting that matters for "
                  "discovery: prediction for alloys from families absent from the training data. The main conclusions are:"),
            ("numbered", [
                "Conformal intervals calibrated on randomly held-out alloys lose their guarantee under alloy-family extrapolation. "
                f"Nominal 90% intervals covered {rc_range(V, 'system')} of alloys from unseen chemical systems and "
                f"{rc_range(V, 'cluster')} from unseen composition clusters.",
                "Family-calibrated conformal prediction (FCP), i.e. CV+ with family-grouped folds and a leakage-free, "
                "novelty-aware scale model, restored mean coverage to "
                f"{g('system', 'FCP'):.3f} and {g('cluster', 'FCP'):.3f}. It reduced the coverage shortfall relative to seven of "
                "eight baselines and improved the interval score relative to six (12 dataset-protocol cells, Holm-corrected). In "
                "a lower-bound screen for high-performing alloys it cut false discoveries three- to four-fold relative to "
                "split conformal prediction, at the cost of lower recall.",
                "Grouping the calibration folds by family is the decisive ingredient. The ensemble-spread scale improves efficiency, "
                "and the compositional-novelty scale equalizes coverage across novelty levels at a small efficiency cost.",
                "Random-forest tree-spread intervals were an unexpectedly strong but uncalibrated competitor; their robustness "
                "comes from systematic over-coverage in-distribution. Normalizing family-grouped CV+ by that tree spread (FCP-RFσ, "
                "formulated post hoc) reached the same efficiency with calibrated coverage and is the best-performing calibrated "
                "variant found here.",
                "Remaining failures concentrate in families with extreme property values and, metallurgically, in multiphase "
                "alloys and the VEC band between BCC- and FCC-stable compositions, where small composition changes alter the "
                "phase constitution. Interval estimates for such candidates should be treated with additional caution, and a "
                "phase-boundary-aware difficulty signal is a natural next step.",
                "FCP certifies coverage against the novelty encoded by the family definition, and nothing beyond it. "
                "Calibrating on a finer family definition than the actual shift lowered coverage. A chronological test showed "
                "nominal coverage when newly reported alloys came from new chemical systems, but no method, FCP included, "
                "covered a shift caused by new processing routes within known systems.",
            ], "numbers2"),
            ]


def declarations(V):
    return [("h1", "CRediT authorship contribution statement"),
            ("p", "[Author 1]: Conceptualization, Methodology, Software, Formal analysis, Investigation, Data curation, "
                  "Visualization, Writing – original draft. [Author 2]: Supervision, Validation, Writing – review & editing. "
                  "(To be completed by the authors.)"),
            ("h1", "Declaration of competing interest"),
            ("p", "The authors declare that they have no known competing financial interests or personal relationships that could "
                  "have appeared to influence the work reported in this paper."),
            ("h1", "Data and code availability"),
            ("p", "All six datasets are public (Table {{tab:datasets}}). The complete code is provided as supplementary material and will be "
                  "deposited in a public repository with a DOI upon acceptance [repository URL to be inserted]. It includes data "
                  "download, cleaning, featurization, all methods, the experiment driver (run_all.py), statistical analysis and "
                  "figure/table generation. Every number in this article is regenerated by `python run_all.py --mode full`."),
            ("h1", "Declaration of generative AI and AI-assisted technologies in the writing process"),
            ("p", "During the preparation of this work the author(s) used an AI assistant (Claude, Anthropic) to assist with code "
                  "development, data analysis and drafting of the manuscript. After using this tool, the author(s) reviewed and "
                  "edited the content as needed and take(s) full responsibility for the content of the published article."),
            ("h1", "Acknowledgements"),
            ("p", "[To be completed by the authors.] The authors thank the creators of the MPEA, Matbench, SuperCon/UCI and matminer "
                  "datasets for making their data public."),
            ("h1", "Funding"),
            ("p", "[To be completed by the authors.]")]
TITLE = ("Prediction intervals for alloys from unseen families: family-calibrated conformal prediction for "
         "machine-learned alloy properties")


def temporal_sentence(V):
    tp = TAB / "table_temporal.csv"
    if not tp.exists():
        return ""
    T = pd.read_csv(tp).set_index(["task", "method"])
    ok = (T.loc[("mpea_ys", "FCP"), "coverage"] >= 0.88 and T.loc[("mpea_hv", "FCP"), "coverage"] < 0.8
          and T.loc[("mpea_hv", "SCP"), "coverage"] < 0.8)
    claim(ok, "abstract temporal sentence supported by table_temporal")
    return ("In a chronological test, FCP reached nominal coverage where new alloys came from new chemical systems but, like "
            "every method, not where new processing routes shifted known systems. ")


def abstract(V):
    g = V["g"]
    a = (f"Machine-learning models are increasingly used to screen alloys from chemical systems that have never been measured, "
         f"yet their uncertainty estimates are validated on randomly held-out alloys. We show that this practice fails under "
         f"alloy-family extrapolation. Across {V['n_tasks']} public datasets (multi-principal-element alloy hardness and yield "
         f"strength, steel yield strength, and three inorganic-compound properties), nominal 90% conformal intervals calibrated "
         f"on random splits covered only {rc_range(V, 'system')} of alloys from unseen "
         f"chemical systems and {rc_range(V, 'cluster')} from unseen composition clusters. "
         f"We propose family-calibrated conformal prediction (FCP): CV+ intervals whose calibration folds hold out whole alloy "
         f"families, with scores normalized by a leakage-free scale built from family-bagged ensemble disagreement and "
         f"compositional novelty. A family-weighted variant targets family-level coverage, and the finite-sample condition for "
         f"its validity is stated explicitly. In {V['n_runs']} evaluation runs (6 datasets × 3 split protocols × 10 seeds) against eight interval "
         f"methods, FCP restored mean coverage to {g('system', 'FCP'):.3f} and {g('cluster', 'FCP'):.3f}. It reduced the coverage "
         f"shortfall relative to seven baselines and the interval score relative to six (Holm-corrected Wilcoxon tests). "
         f"Ablations identify family-grouped calibration as the decisive component. Uncalibrated random-forest tree-spread "
         f"intervals were competitive under shift but over-covered in-distribution; calibrating that spread at the family level "
         f"(a post hoc variant) matched their efficiency while staying calibrated. {temporal_sentence(V)}"
         f"Remaining failures concentrate in families with extreme property values. "
         f"All results are reproducible from public data.")
    n = len(a.split())
    claim(n <= 250, f"abstract has {n} words (<= 250)")
    return a


KEYWORDS = ["Alloy design", "High-entropy alloys", "Machine learning", "Uncertainty quantification", "Conformal prediction",
            "Out-of-distribution generalization", "Materials informatics"]


def highlights(V):
    g = V["g"]
    h = [f"Random-split 90% conformal intervals cover only {min(g(p, m) for p in ['system', 'cluster'] for m in RC) * 100:.0f}–{max(g(p, m) for p in ['system', 'cluster'] for m in RC) * 100:.0f}% of new-family alloys",
         "Family-grouped CV+ calibration restores mean coverage near 90% for new families",
         "Leakage-free scale from ensemble spread and novelty adapts the interval width",
         "Benchmark: 6 datasets, 3 shift protocols, 17 interval methods, 10 seeds",
         "Remaining misses concentrate in alloy families with extreme property values"]
    for x in h:
        claim(len(x) <= 85, f"highlight <= 85 characters: {x} ({len(x)})")
    return h


def design(V):
    return [("h1", "6. Research questions and experiments"),
            ("p", "Each research question was mapped to one pre-specified experiment, and each claim in Sections 7–11 refers to "
                  "one of them. Exp. 1 (main evaluation, RQ1–RQ2): all methods × 6 tasks × 3 protocols × 10 seeds × α ∈ "
                  "{0.05, 0.1, 0.2}. Exp. 2 (baselines): the eight comparison methods of Section 5.4 within Exp. 1. Exp. 3 "
                  "(ablation, RQ3): ten CV+ variants that differ only in fold grouping, scale model and weights. Exp. 4 (robustness, "
                  "RQ4): Gaussian label noise of 0.10 and 0.25 SD(y), and training on 50% of the training families (system "
                  "protocol, 5 seeds). Exp. 5 (generalization, RQ5): a mis-specified family definition in which FCP calibrates on "
                  "chemical systems while the test shift is composition clusters, together with a base-learner swap to random-forest "
                  "members and a random (unbalanced) assignment of clusters to outer folds. Exp. 6 (computational cost): wall time "
                  "and peak memory per outer fold. Exp. 7 (sensitivity): one-factor-at-a-time variation of *K*, *M*, φ and "
                  "*k*_{nn}. Exp. 8 (error analysis): per-family coverage against novelty, property extremity and family size.")]


def build(V):
    allk = dict(S.CITE_KEYS)
    bib = Bib(load_bib(allk, S.MANUAL))
    blocks = []

    def add(items):
        for it in items:
            kind, val = it[0], it[1]
            if kind == "h1":
                blocks.append({"type": "heading", "level": 1, "text": val})
            elif kind == "h2":
                blocks.append({"type": "heading", "level": 2, "text": val})
            elif kind == "p":
                blocks.append({"type": "para", "runs": runs(bib.cite(val))})
            elif kind == "bullets":
                blocks.append({"type": "bullets", "items": [runs(bib.cite(x)) for x in val]})
            elif kind == "numbered":
                blocks.append({"type": "numbered", "items": [runs(bib.cite(x)) for x in val], "ref": it[2] if len(it) > 2 else "numbers"})
            elif kind == "eq":
                blocks.append({"type": "equation", "eq": val})
            elif kind == "fig":
                blocks.append(fig_block(*val))
            elif kind.startswith("table"):
                tb = TB[kind]
                if tb.get("_placed"):
                    raise ValueError("table placed twice: " + kind)
                tb["_placed"] = True
                tb["caption"] = [dict(r, t=bib.cite(r["t"])) for r in tb["caption"]]
                tb["rows"] = [[bib.cite(c) if isinstance(c, str) else c for c in row] for row in tb["rows"]]
                blocks.append(tb)
    # title page
    blocks += [{"type": "title", "text": TITLE},
               {"type": "center", "runs": runs("[Author 1]^{a,*}, [Author 2]^{a}")},
               {"type": "center", "runs": runs("^{a} [Department, Institution, City, Country]"), "size": 20},
               {"type": "center", "runs": runs("^{*} Corresponding author: [e-mail address]"), "size": 20}]
    blocks.append({"type": "heading", "level": 1, "text": "Abstract"})
    blocks.append({"type": "para", "runs": runs(abstract(V))})
    blocks.append({"type": "label", "runs": runs("**Keywords:** " + "; ".join(KEYWORDS))})
    global TB
    TB = tables(V, bib)
    for sec in [S.intro, S.related, S.gap, S.method, S.setup, design, results, screening, metallurgy_section, ablation, robustness_sections,
                computational, error_analysis, discussion, limitations, conclusion, declarations]:
        add(sec(V))
    blocks.append({"type": "heading", "level": 1, "text": "References"})
    blocks.append({"type": "refs", "items": [runs(x) for x in bib.formatted()]})
    number_refs(blocks)
    spec = {"meta": {"title": TITLE, "line_numbers": True, "description": "Manuscript for Journal of Materials Research and Technology"},
            "blocks": blocks}
    return spec, bib


def number_refs(blocks):
    """Assign figure/table numbers in order of first appearance of {{fig:x}}/{{tab:x}} and substitute everywhere."""
    import re
    order = {"fig": [], "tab": []}
    texts = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "t" and isinstance(v, str):
                    texts.append(v)
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(blocks)
    for t in texts:
        for kind, key in re.findall(r"\{+(fig|tab):(\w+)\}+", t):
            if key not in order[kind]:
                order[kind].append(key)

    def sub(o):
        if isinstance(o, dict):
            for k, v in list(o.items()):
                if k == "t" and isinstance(v, str):
                    o[k] = re.sub(r"\{+(fig|tab):(\w+)\}+", lambda m: str(order[m.group(1)].index(m.group(2)) + 1), v)
                else:
                    sub(v)
        elif isinstance(o, list):
            for v in o:
                sub(v)
    sub(blocks)
    NUMBERING.update(order)


NUMBERING = {}


def SENS_HOOK(V):
    return []


def additional_checks(V):
    """Compact summary of three secondary checks; full tables and figures are in the Supplementary Material."""
    se = V["sensitivity"]
    d = se[(se.alpha == 0.1) & (se.method == "FCP")]
    g = d.groupby(["parameter", "value"]).agg(cov=("coverage", "mean"), isc=("interval_score_sd", "mean"))
    claim(g["cov"].min() >= 0.9, "FCP coverage >= 0.9 for all sensitivity settings")
    rf = pd.read_csv(TAB / "table_randfolds.csv").set_index(["method", "assignment"])
    rq = lambda m, a, k="mean_coverage": float(rf.loc[(m, a), k])
    claim(abs(rq("FCP", "random") - rq("FCP", "balanced (main)")) < 0.03, "FCP coverage robust to fold assignment")
    claim(rq("SCP", "random") < 0.8 and rq("CV+", "random") < 0.8, "random-calibrated still under-cover with random assignment")
    mo = pd.read_csv(TAB / "table_mondrian.csv").set_index(["protocol", "method"])
    mq = lambda p, m, k="mean_coverage": float(mo.loc[(p, m), k])
    claim(mq("cluster", "MCP") < mq("cluster", "FCP") - 0.03 and mq("cluster", "MCP") >= mq("cluster", "SCP"), "Mondrian between SCP and FCP")
    return [("h2", "9.6. Additional checks"),
            ("p", ("Four" if (RES / "statistics_fcps.json").exists() else "Three") + " further checks are summarized here; full results are in the Supplementary Material. (i) **Sensitivity.** "
                  "Varying the number of folds (*K* ∈ {3, 10}), ensemble members (*M* ∈ {3, 12}), family fraction (φ ∈ {0.5, 0.9}) "
                  f"and *k*_{{nn}} ∈ {{1, 15}} one at a time kept FCP's coverage between {g['cov'].min():.3f} and {g['cov'].max():.3f} "
                  f"(interval score {g['isc'].min():.2f}–{g['isc'].max():.2f}; Supplementary Fig. {SFIG['sens']}), so validity does "
                  "not hinge on tuning. (ii) **Randomized cluster-to-fold assignment.** The size-balanced assignment of ten clusters to "
                  "five outer folds is identical for every seed; with a fully random assignment per seed, mean coverage was "
                  f"{rq('FCP', 'random'):.3f} for FCP (balanced: {rq('FCP', 'balanced (main)'):.3f}), {rq('SCP', 'random'):.3f} for SCP "
                  f"and {rq('CV+', 'random'):.3f} for CV+. (iii) **Novelty-conditional (Mondrian) calibration** with random splits "
                  f"(MCP, separate quantiles in novelty tertiles) covered {mq('system', 'MCP'):.3f} (system) and "
                  f"{mq('cluster', 'MCP'):.3f} (cluster), between SCP ({mq('cluster', 'SCP'):.3f}) and FCP ({mq('cluster', 'FCP'):.3f}) "
                  "under cluster holdout: conditioning on distance helps, but a randomly held-out alloy that looks novel still has "
                  "relatives of its own family in the training data, which a genuinely new family does not.")] + fcps_check()


def fcps_check():
    """(iv) Empirical check of Proposition 1: FCP-S (one random calibration alloy per family)."""
    p = RES / "statistics_fcps.json"
    if not p.exists():
        return []
    f = json.load(open(p))
    t = pd.read_csv(TAB / "table_fcps.csv"); t = t[t.alpha == 0.1]
    mean = f["mean"]; mn = f["min_task_family_coverage"]
    fc = lambda m: mean["family_coverage"][m]
    isc = lambda m: mean["interval_score_sd"][m]
    w = f["FCP-S vs FCP-W interval_score (task x seed)"]
    above = f["all_cells_above_bound"]
    price = np.isfinite(isc("FCP-S")) and np.isfinite(isc("FCP-W")) and isc("FCP-S") > isc("FCP-W") and w["p"] < 0.05
    txt = ("(iv) **Proposition 1 in practice.** FCP-S, the family-subsampled variant covered by Proposition 1, was run on the six "
           f"tasks under unseen-system holdout (10 seeds; *G* = {int(t.G_train.min())}–{int(t.G_train.max())} training families, for "
           f"which the bound evaluates to {f['min_bound']:.3f}–{f['max_bound']:.3f} at α = 0.1). Its family-level coverage averaged "
           f"{fc('FCP-S'):.3f} (worst task {mn['FCP-S']:.3f}), against {fc('FCP-W'):.3f} for FCP-W and {fc('FCP'):.3f} for FCP; "
           + ("every task-level mean exceeded the bound. " if above else "some task-level means fell below the bound (Supplementary Material). ")
           + (f"Keeping only one calibration alloy per family costs efficiency: the interval score of FCP-S exceeded that of "
              f"FCP-W ({isc('FCP-S'):.2f} vs {isc('FCP-W'):.2f}; paired Wilcoxon over task–seed cells, p = {w['p']:.2g}). The "
              "guarantee is thus available at a measurable price, and the deterministic weights of FCP-W are the practical choice "
              "when family-level coverage is the target." if price else
              f"The interval scores of FCP-S and FCP-W were {isc('FCP-S'):.2f} and {isc('FCP-W'):.2f} (paired Wilcoxon over task–seed "
              f"cells, p = {w['p']:.2g}), so in these data the guarantee comes without a detectable loss of efficiency."))
    return [("p", txt)]


def basemodel_section(V):
    bp = TAB / "table_basemodel.csv"
    if not bp.exists():
        return []
    b = pd.read_csv(bp).set_index(["protocol", "method"])
    q = lambda p, m, k="mean_coverage": float(b.loc[(p, m), k])
    bt = json.load(open(RES / "statistics_basemodel.json"))
    t_rz = bt["FCP [RF] vs RF-z (interval_score_sd)"]; t_cv = bt["FCP [RF] vs CV+ [RF] (shortfall)"]
    for p in ["system", "cluster"]:
        claim(abs(q(p, "FCP [RF]") - q(p, "FCP [LGBM]")) < 0.015, f"FCP coverage with RF members within 1.5 points of LGBM ({p})")
        claim(q(p, "CV+ [RF]") < 0.88, f"random-fold CV+ with RF members under-covers ({p})")
    claim(t_rz["median_diff"] > 0 and t_rz["p"] < 0.01, "RF-z interval score significantly better than FCP[RF]")
    claim(t_cv["median_diff"] < 0 and t_cv["p"] < 0.01, "FCP[RF] shortfall significantly smaller than CV+[RF]")
    E = [("h2", "9.4. Base-learner swap and random-forest tree spread"),
         ("p", "Is the effect of family-level calibration specific to LightGBM, and can it be combined with the efficiency of "
               "random forests? FCP and the main baselines were re-run with the ensemble members replaced by random forests "
               "(6 members of 50 trees, all tasks and protocols, seeds 0–4). Coverage with forest members was practically "
               f"unchanged: FCP covered {q('system', 'FCP [RF]'):.3f} (system) and {q('cluster', 'FCP [RF]'):.3f} (cluster), "
               f"against {q('system', 'FCP [LGBM]'):.3f} and {q('cluster', 'FCP [LGBM]'):.3f} with LightGBM members. Random-fold "
               f"CV+ with the same forests under-covered just as before ({q('system', 'CV+ [RF]'):.3f} and "
               f"{q('cluster', 'CV+ [RF]'):.3f}). FCP[RF]'s shortfall was smaller in the paired comparison (12 cells, "
               f"p = {t_cv['p']:.4f}). The failure of random-split calibration and its repair by family-level calibration are "
               "therefore properties of the calibration, not of the regressor. However, FCP with forest members did not match "
               f"RF-z's interval score: RF-z was better in the paired comparison (median difference {t_rz['median_diff']:+.2f} SD, "
               f"p = {t_rz['p']:.4f})."),
         ]
    rp = RES / "rfsigma_results.csv"
    if rp.exists():
        r = pd.read_csv(rp); r = r[r.alpha == 0.1]
        c = r.groupby(["task", "protocol", "method"]).agg(cov=("coverage", "mean"), isc=("interval_score_sd", "mean")).reset_index()
        m = c.groupby(["protocol", "method"]).agg(cov=("cov", "mean"), isc=("isc", "mean"), mn=("cov", "min"))
        mm = lambda p, k, f="cov": float(m.loc[(p, k), f])
        sh = c[c.protocol.isin(["system", "cluster"])]
        from scipy.stats import wilcoxon
        P = sh.pivot_table(index=["task", "protocol"], columns="method", values="isc")
        pv = wilcoxon(P["FCP-RFsigma"], P["RF-z"]).pvalue
        Cv = sh.pivot_table(index=["task", "protocol"], columns="method", values="cov")
        RFSIG.update(cov_sys=mm("system", "FCP-RFsigma"), cov_cl=mm("cluster", "FCP-RFsigma"))
        E.append(("p", "We then tested a specific explanation (hypothesis recorded before the run; Supplementary iteration log): "
                       "RF-z's efficiency comes from its per-tree spread, so family-grouped CV+ normalized directly by that spread "
                       "(FCP-RFσ) should be both calibrated and efficient. FCP-RFσ covered "
                       f"{mm('system', 'FCP-RFsigma'):.3f} (system) and {mm('cluster', 'FCP-RFsigma'):.3f} (cluster), with interval "
                       f"scores {mm('system', 'FCP-RFsigma', 'isc'):.2f} and {mm('cluster', 'FCP-RFsigma', 'isc'):.2f}, against "
                       f"RF-z's {mm('system', 'RF-z'):.3f} / {mm('cluster', 'RF-z'):.3f} and {mm('system', 'RF-z', 'isc'):.2f} / "
                       f"{mm('cluster', 'RF-z', 'isc'):.2f} (paired interval-score test p = {pv:.4f}). The random-fold version covered "
                       f"{mm('system', 'CV+-RFsigma'):.3f} / {mm('cluster', 'CV+-RFsigma'):.3f}. " + RFSIG_VERDICT(m, pv)))
    return E


RFSIG = {}


def RFSIG_VERDICT(m, pv):
    """Verdict from the data: coverage near nominal and interval score not significantly different from RF-z."""
    r = pd.read_csv(RES / "rfsigma_results.csv"); f = pd.read_csv(RES / "raw_results.csv")
    f = f[(f.method == "FCP") & f.seed.isin(r.seed.unique())]
    a = pd.concat([r, f])
    c = a[a.alpha == 0.1].groupby(["task", "protocol", "method"]).interval_score_sd.mean().unstack()
    sh = c.loc[(slice(None), ["system", "cluster"]), :]
    from scipy.stats import wilcoxon
    p_fcp = wilcoxon(sh["FCP-RFsigma"], sh["FCP"]).pvalue
    w_fcp = int((sh["FCP-RFsigma"] < sh["FCP"]).sum())
    cal = a.groupby(["protocol", "method", "alpha"]).coverage.mean()
    rs, rz = cal[("random", "FCP-RFsigma", 0.2)], cal[("random", "RF-z", 0.2)]
    rs1, rz1 = cal[("random", "FCP-RFsigma", 0.1)], cal[("random", "RF-z", 0.1)]
    cov_ok = m.loc[("system", "FCP-RFsigma"), "cov"] >= 0.9 and m.loc[("cluster", "FCP-RFsigma"), "cov"] >= 0.9
    claim(cov_ok, "FCP-RFsigma mean coverage >= 0.9 under both shifts")
    claim(pv > 0.05, "FCP-RFsigma vs RF-z interval score not significantly different")
    claim(p_fcp < 0.01 and w_fcp >= 10, "FCP-RFsigma interval score better than LightGBM FCP")
    claim(abs(rs - 0.8) < abs(rz - 0.8) and abs(rs1 - 0.9) < abs(rz1 - 0.9), "FCP-RFsigma better calibrated than RF-z in-distribution")
    RFSIG.update(p_fcp=p_fcp, w_fcp=w_fcp, rs=rs, rz=rz, rs1=rs1, rz1=rz1)
    return (f"The hypothesis was supported. FCP-RFσ's interval score was statistically indistinguishable from RF-z's and "
            f"better than that of the LightGBM-based FCP in {w_fcp} of 12 shift cells (p = {p_fcp:.4f}). Unlike RF-z, it stayed "
            f"calibrated in-distribution: {rs1:.3f} and {rs:.3f} at nominal 0.90 and 0.80, against {rz1:.3f} and {rz:.3f} for RF-z. "
            "Because this variant was formulated after the main results, it is reported as a post hoc finding to be confirmed "
            "on further data. It is, however, the best-performing calibrated method in this study.")


def screening(V):
    sp = pd.read_csv(TAB / "table_screening_pooled.csv").set_index("method")
    st = pd.read_csv(TAB / "table_screening.csv")
    ys = st[st.task == "mpea_ys"].set_index("method")
    claim(sp.loc["FCP", "fdp"] < sp.loc["SCP", "fdp"] / 2 and sp.loc["FCP", "fdp"] < sp.loc["CV+", "fdp"] / 2, "FCP halves FDP vs SCP/CV+")
    claim(2.5 < sp.loc["SCP", "fdp"] / sp.loc["FCP", "fdp"] < 4.5 and 2.5 < sp.loc["CV+", "fdp"] / sp.loc["FCP", "fdp"] < 4.5, "FDP ratio three- to four-fold (2.5-4.5)")
    claim(all(sp.loc[m, "fdp"] < 0.05 for m in ["SCP", "CV+", "FCP"]), "pooled FDP below 5% for SCP, CV+, FCP")
    claim(ys.loc["SCP", "fdp"] > 0.10, "MPEA YS SCP FDP > 10%")
    claim(sp.loc["FCP", "recall"] < sp.loc["SCP", "recall"], "FCP recall lower than SCP")
    claim(sp.loc["RF-z", "fdp"] < sp.loc["FCP", "fdp"] and sp.loc["RF-z", "recall"] < sp.loc["FCP", "recall"], "RF-z more conservative")
    claim(ys.loc["FCP", "fdp"] < ys.loc["SCP", "fdp"], "MPEA-YS FCP fewer false discoveries")
    rows = []
    for m in ["SCP", "CV+", "CQR", "GP", "RF-z", "GSCP", "FCP"]:
        r = [m]
        for t in ["mpea_hv", "mpea_ys", "steel_ys", "superhard_k", "supercon_tc"]:
            x = st[(st.task == t) & (st.method == m)].iloc[0]
            r.append(f"{x.n_selected:.1f} / " + ("–" if not np.isfinite(x.fdp) else f"{x.fdp * 100:.0f}%"))
        r += [f"{sp.loc[m, 'fdp'] * 100:.1f}%", f"{sp.loc[m, 'recall']:.2f}"]
        rows.append(r)
    TB["table_screening"] = {"type": "table", "font_size": 15,
        "caption": runs("**Table {{tab:screening}}.** Screening for high performers under unseen-chemical-system holdout (α = 0.1). An "
                        "alloy is selected if the lower bound of its interval exceeds the upper quartile τ of the task's property. "
                        "Per task: mean number selected per seed / false-discovery proportion (selected alloys with measured "
                        "property < τ). Pooled over 5 tasks × 10 seeds: false-discovery proportion (FDP) and recall of all alloys "
                        "with property ≥ τ."),
        "header": ["Method", "MPEA HV", "MPEA YS", "Steel YS", "Bulk mod.", "Tc", "Pooled FDP", "Recall"],
        "rows": rows, "col_widths": [0.1, 0.12, 0.12, 0.12, 0.13, 0.15, 0.13, 0.13]}
    return [("h2", "7.5. Consequences for alloy screening"),
            ("p", "Interval validity matters for decisions. A common use of intervals in alloy design is to accept a candidate "
                  "only if even its pessimistic (lower-bound) prediction exceeds a target. We emulated this under unseen-chemical-"
                  "system holdout: an alloy was 'selected' when its lower bound exceeded the upper quartile τ of the property "
                  f"(Table {{tab:screening}}). Pooled over five tasks and ten seeds, {sp.loc['SCP', 'fdp'] * 100:.1f}% of the alloys "
                  f"selected with SCP and {sp.loc['CV+', 'fdp'] * 100:.1f}% of those selected with CV+ were false discoveries, "
                  f"against {sp.loc['FCP', 'fdp'] * 100:.1f}% with FCP. For MPEA yield strength the false-discovery proportion fell "
                  f"from {ys.loc['SCP', 'fdp'] * 100:.0f}% (SCP) to {ys.loc['FCP', 'fdp'] * 100:.0f}% (FCP). The gain is not free: "
                  f"FCP recovered {sp.loc['FCP', 'recall'] * 100:.0f}% of the true high performers against "
                  f"{sp.loc['SCP', 'recall'] * 100:.0f}% for SCP. RF-z was more conservative still (false discoveries "
                  f"{sp.loc['RF-z', 'fdp'] * 100:.1f}%, recall {sp.loc['RF-z', 'recall'] * 100:.0f}%), and CQR's wide quantile "
                  f"intervals almost never cleared the threshold. Pooled over tasks, all methods kept the false-discovery "
                  "proportion below the 5% that a 95% one-sided lower bound would suggest, but this hides large task-level "
                  f"differences: for MPEA yield strength, SCP's {ys.loc['SCP', 'fdp'] * 100:.0f}% far exceeds it. "
                  f"Relative to FCP, SCP and CV+ admitted {sp.loc['SCP', 'fdp'] / sp.loc['FCP', 'fdp']:.1f} and "
                  f"{sp.loc['CV+', 'fdp'] / sp.loc['FCP', 'fdp']:.1f} times as large a proportion of false discoveries."),
            ("table_screening", None)]


def robustness_sections(V):
    E = [("h1", "9. Robustness and generalization")]
    rb = V["robustness"]
    if rb is not None:
        r = rb[(rb.alpha == 0.1) & (rb.method != "GP")]
        t = r.groupby(["condition", "method"]).agg(cov=("coverage", "mean"), mn=("coverage", "min"), isc=("interval_score_sd", "mean"))
        c = lambda cond, m, k="cov": float(t.loc[(cond, m), k])
        conds = ["label_noise=0.1", "label_noise=0.25", "train_fraction=0.5"]
        for cd in conds:
            claim(c(cd, "FCP") >= 0.9, f"FCP mean coverage >= 0.9 under {cd}")
            claim(c(cd, "SCP") < 0.88 and c(cd, "CV+") < 0.89, f"SCP/CV+ under-cover under {cd}")
        fmin = min(c(cd, "FCP", "mn") for cd in conds)
        E += [("h2", "9.1. Label noise and reduced training data (RQ4)"),
              ("p", "Fig. {{fig:robust}} reports coverage under the unseen-chemical-system protocol (5 seeds, all tasks except the "
                    "superconductors) when Gaussian noise of 0.10 or 0.25 SD(y) was added to the labels, or when only half of the "
                    "training families were available. FCP's mean coverage stayed at "
                    f"{c(conds[0], 'FCP'):.3f}, {c(conds[1], 'FCP'):.3f} and {c(conds[2], 'FCP'):.3f}, and its worst dataset at "
                    f"{fmin:.3f} or above. SCP ({c(conds[0], 'SCP'):.3f}, {c(conds[1], 'SCP'):.3f}, {c(conds[2], 'SCP'):.3f}) and "
                    f"CV+ ({c(conds[0], 'CV+'):.3f}, {c(conds[1], 'CV+'):.3f}, {c(conds[2], 'CV+'):.3f}) remained below nominal, "
                    "and the shortfall of SCP grew when training data were halved. Label noise widens all intervals but does not "
                    "change the ranking: the calibration mismatch, not the noise level, drives the under-coverage. RF-z again "
                    f"covered well ({c(conds[0], 'RF-z'):.3f}–{c(conds[2], 'RF-z'):.3f}) with a slightly lower interval score than FCP."),
              ("fig", ("fig8_robustness", "Fig. {{fig:robust}}. Coverage under label noise and reduced training data "
                       "(unseen-chemical-system protocol, α = 0.1, mean over five datasets and five seeds)."))]
    ge = V["generalization"]
    if ge is not None:
        g = ge[ge.alpha == 0.1].groupby(["task", "method"]).coverage.mean().unstack()
        m = g.mean()
        claim(m["FCP"] < V["g"]("cluster", "FCP") - 0.05, "mis-specified families reduce FCP coverage substantially")
        claim(m["FCP"] > m["SCP"] + 0.05 and m["FCP"] > m["GSCP"], "FCP still better than SCP/GSCP under mis-specification")
        claim(m["FCP"] < 0.9, "FCP below nominal under mis-specification")
        E += [("h2", "9.2. Mis-specified family definition (RQ5)"),
              ("p", "In practice the family definition used for calibration may not match the novelty that is actually explored. "
                    "We calibrated FCP on chemical systems (F1) while the test alloys came from unseen composition clusters (F2), "
                    "a coarser and harder shift. Mean coverage then fell to "
                    f"{m['FCP']:.3f} for FCP and {m['FCP-W']:.3f} for FCP-W, against {V['g']('cluster', 'FCP'):.3f} when calibration "
                    f"used the matching cluster families. The random-calibrated methods fell further (SCP {m['SCP']:.3f}, CV+ "
                    f"{m['CV+']:.3f}), and so did the family-held-out split GSCP ({m['GSCP']:.3f}). The task-wise minimum for FCP "
                    f"was {g['FCP'].min():.3f} ({TASK[g['FCP'].idxmin()]}). FCP thus degrades gracefully, remaining the best of the "
                    "methods compared, but it is not a substitute for choosing a family definition at least as coarse as the "
                    "intended exploration. A practical rule follows: when in doubt, calibrate on the coarser family definition."),
              ]
    tp = TAB / "table_temporal.csv"
    if tp.exists():
        T = pd.read_csv(tp).set_index(["task", "method"])
        q = lambda t, m, k="coverage": float(T.loc[(t, m), k])
        claim(q("mpea_ys", "FCP") >= 0.88 and q("mpea_ys", "SCP") < 0.8, "temporal: FCP near nominal for MPEA YS, SCP not")
        claim(q("mpea_ys", "FCP", "cov_unseen_system") > q("mpea_ys", "SCP", "cov_unseen_system") + 0.1, "temporal YS: FCP fixes unseen systems")
        claim(q("mpea_hv", "FCP") < 0.8 and q("mpea_hv", "SCP") < 0.8, "temporal HV: all fail")
        claim(q("mpea_hv", "FCP", "cov_seen_system") < q("mpea_hv", "FCP", "cov_unseen_system"), "temporal HV failure concentrated in seen systems")
        claim(q("mpea_hv", "FCP", "bias") > 50, "temporal HV: positive bias > 50 HV")
        claim(q("mpea_ys", "RF-z") >= 0.88 and q("mpea_ys", "GP") >= 0.88, "temporal YS: RF-z and GP also near nominal")
        E += [("h2", "9.3. Chronological deployment test"),
              ("p", "Family holdouts are constructed shifts. A more realistic test trains on alloys published before 2019 and "
                    "predicts those first reported in 2019, the most recent year in the MPEA database (10 seeds; Table {{tab:temporal}}). "
                    f"For yield strength, {q('mpea_ys', 'FCP', 'frac_unseen') * 100:.0f}% of the 2019 alloys belong to chemical systems "
                    f"absent from earlier years. FCP covered {q('mpea_ys', 'FCP'):.3f} of them overall and "
                    f"{q('mpea_ys', 'FCP', 'cov_unseen_system'):.3f} of those in new systems, against {q('mpea_ys', 'SCP'):.3f} and "
                    f"{q('mpea_ys', 'SCP', 'cov_unseen_system'):.3f} for SCP and {q('mpea_ys', 'CV+'):.3f} overall for CV+. The "
                    f"uncalibrated RF-z ({q('mpea_ys', 'RF-z'):.3f}) and the GP ({q('mpea_ys', 'GP'):.3f}) also reached the nominal "
                    "level in this test, so FCP was not unique here. Under a genuine chronological shift whose main component is "
                    "family novelty, family-level calibration delivered nominal coverage where random-split calibration did not."),
              ("p", f"Hardness behaved differently. Every method failed (FCP {q('mpea_hv', 'FCP'):.3f}, SCP {q('mpea_hv', 'SCP'):.3f}, "
                    f"CV+ {q('mpea_hv', 'CV+'):.3f}). The failure was concentrated in chemical systems that *were* present in the "
                    f"training years (FCP: {q('mpea_hv', 'FCP', 'cov_seen_system'):.3f} in seen vs "
                    f"{q('mpea_hv', 'FCP', 'cov_unseen_system'):.3f} in unseen systems). The predictions were biased by "
                    f"{q('mpea_hv', 'FCP', 'bias'):+.0f} HV on average, and the 2019 entries included more powder-processed alloys and "
                    "more entries with unreported processing. This is a shift in the composition–property relation *within* known "
                    "families, plausibly caused by new processing routes and measurement practice. No calibration on historical "
                    "data, family-level or otherwise, can anticipate it. It marks the boundary of what FCP addresses: novelty of "
                    "the alloy family, not changes in how alloys of known families are made or measured."),
              ("table_temporal", None)]
        rows = []
        for t in ["mpea_hv", "mpea_ys"]:
            for m in ["SCP", "CV+", "CQR", "WCP", "GP", "RF-z", "GSCP", "FCP", "FCP-W"]:
                if (t, m) in T.index:
                    rows.append([TASK[t], m, f"{q(t, m):.3f} ± {q(t, m, 'coverage_sd'):.3f}", f"{q(t, m, 'cov_seen_system'):.3f}",
                                 f"{q(t, m, 'cov_unseen_system'):.3f}"])
        TB["table_temporal"] = {"type": "table", "font_size": 16,
            "caption": runs("**Table {{tab:temporal}}.** Chronological test on MPEA data (train: publication year < 2019; test: "
                            "2019). Coverage (mean ± SD over 10 seeds) overall and for test alloys whose chemical system does or "
                            "does not occur in the training years."),
            "header": ["Task", "Method", "Coverage", "Seen systems", "Unseen systems"], "rows": rows,
            "col_widths": [0.26, 0.14, 0.22, 0.19, 0.19]}
    E += SENS_HOOK(V)
    return E


def computational(V):
    d = V["df"]; d = d[d.alpha == 0.1]
    t = d.groupby(["task", "method"]).fit_time_s_per_fold.mean().unstack()
    ratio_cv = (t["FCP"] / t["CV+"])
    ratio_scp = (t["FCP"] / t["SCP"])
    claim((ratio_cv - 1).abs().max() < 0.1, "FCP cost within 10% of random-fold CV+")
    claim(ratio_scp.min() > 3 and ratio_scp.max() < 8, "FCP costs 3-8x SCP")
    claim(all(t.loc[k, "GP"] > t.loc[k, "FCP"] for k in ["mpea_ys", "expt_hf", "supercon_tc", "superhard_k"]), "GP slower than FCP on 4 larger tasks")
    rows = []
    for k in TASK:
        rows.append([TASK[k]] + [f"{t.loc[k, m]:.1f}" for m in ["SCP", "WCP", "CQR", "GSCP", "CV+", "FCP", "GP", "RF-z"]])
    TB["table_cost"] = {"type": "table", "font_size": 16,
        "caption": runs("**Table {{tab:cost}}.** Mean wall time (s) per outer fold to fit a method and form its intervals for all "
                        "test alloys (single CPU thread; 4 runs executed concurrently on a 4-core machine; α = 0.1). FCP-W and "
                        "the other CV+ variants share FCP's fits."),
        "header": ["Task", "SCP", "WCP", "CQR", "GSCP", "CV+", "FCP", "GP", "RF-z"], "rows": rows,
        "col_widths": [0.24] + [0.095] * 8}
    E = [("h1", "10. Computational cost"),
         ("p", "FCP's cost is dominated by fitting *K* = 5 family-bagged ensembles of *M* = 6 members, i.e. 30 LightGBM models per "
               f"outer fold. It was therefore within {(ratio_cv - 1).abs().max() * 100:.0f}% of random-fold CV+, which fits the same "
               f"number of models, and {ratio_scp.min():.1f}–{ratio_scp.max():.1f} times as expensive as split conformal prediction "
               f"(Supplementary Material). In absolute terms, one outer fold took {t['FCP'].min():.1f}–{t['FCP'].max():.1f} s on a single CPU "
               f"thread for about {int(V['ds'].n.min() * 0.8):,}–{int(V['ds'].n.max() * 0.8):,} training alloys (80% of each task), less than the Gaussian process on the four larger tasks. Forming the "
               "intervals is a weighted quantile over the *n* calibration bounds per test alloy, which adds O(*n* log *n*) per "
               "alloy and is negligible at these sizes. No GPU is required. The extra cost relative to split conformal prediction "
               "is incurred once per model update, not per prediction, which matters little in alloy design, where each new "
               "measurement costs hours to days.")]
    ep = V["efficiency"]
    if ep is not None:
        e = ep.set_index(["task", "method"])
        E[-1] = (E[-1][0], E[-1][1] + f" Measured in isolated processes, the peak resident memory of FCP was "
                 f"{e.xs('FCP', level='method').peak_rss_mb.max():.0f} MB, against {e.xs('GP', level='method').peak_rss_mb.max():.0f} MB "
                 "for the GP (Supplementary Fig. {SFIG['efficiency']}).")
    return E


if __name__ == "__main__":
    V = load()
    spec, bib = build(V)
    (HERE / "spec.json").write_text(json.dumps(spec, ensure_ascii=False))
    (HERE.parent / "highlights.txt").write_text("\n".join(highlights(V)) + "\n")
    uniq = list({c["claim"]: c for c in CLAIMS}.values())
    (HERE.parent / "claim_audit.json").write_text(json.dumps(uniq, indent=1, ensure_ascii=False))
    hs = {"meta": {"title": "Highlights", "line_numbers": False},
          "blocks": [{"type": "heading", "level": 1, "text": "Highlights"},
                     {"type": "bullets", "items": [runs(h) for h in highlights(V)]}]}
    (HERE / "highlights_spec.json").write_text(json.dumps(hs, ensure_ascii=False))
    print("blocks", len(spec["blocks"]), "references", len(bib.order), "unique claims", len({c["claim"] for c in CLAIMS}))
    unused = sorted(set(S.CITE_KEYS) | set(S.MANUAL) - set(bib.order))
    print("uncited keys:", [k for k in unused if k not in bib.order])
