"""Generates every statistic, table and figure from machine-readable results (no manual numbers).

Inputs : results/raw_results.csv, robustness_results.csv, generalization_results.csv, sensitivity_results.csv,
         efficiency_results.csv, results/cache/*.pkl (per-point bounds), tables/dataset_summary.csv
Outputs: results/metrics.json, results/statistics.json, tables/*.csv + *.md, figures/*.png + *.pdf
Primary analysis level: alpha = 0.1 (pre-specified). alpha = 0.05 / 0.2 are secondary.
"""
import json, pickle
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from fcp.statistics import tests as T

TASK_LABEL = {"mpea_hv": "MPEA hardness", "mpea_ys": "MPEA yield strength", "steel_ys": "Steel yield strength",
              "superhard_k": "Bulk modulus", "expt_hf": "Formation enthalpy", "supercon_tc": "Superconductor Tc"}
PROT_LABEL = {"random": "Random (in-distribution)", "system": "Unseen chemical system", "cluster": "Unseen composition cluster"}
KEY = ["SCP", "CV+", "CQR", "WCP", "GP", "RF-z", "Ens-z", "GSCP", "FCP", "FCP-W"]
BASELINES = ["SCP", "CV+", "CQR", "WCP", "GP", "RF-z", "Ens-z", "GSCP"]
ABLATION = ["CV+", "NCV+", "GCV+", "GCV+[spread]", "GCV+[novelty]", "FCP", "GCV+-W", "FCP-W[spread]",
            "FCP-W[novelty]", "FCP-W"]
# palette (validated reference instance; categorical slots in fixed order) — colour encodes the method GROUP,
# marker shape encodes the individual method (secondary encoding)
C_BLUE, C_ORANGE, C_AQUA, C_YELLOW, C_MAGENTA, C_GREEN, C_VIOLET, C_RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
GROUP = {"SCP": ("Random-calibrated conformal", C_ORANGE), "CV+": ("Random-calibrated conformal", C_ORANGE),
         "CQR": ("Random-calibrated conformal", C_ORANGE), "WCP": ("Random-calibrated conformal", C_ORANGE),
         "GP": ("Model-based (uncalibrated)", C_VIOLET), "RF-z": ("Model-based (uncalibrated)", C_VIOLET),
         "Ens-z": ("Model-based (uncalibrated)", C_VIOLET),
         "GSCP": ("Family-calibrated", C_BLUE), "FCP": ("Family-calibrated", C_BLUE), "FCP-W": ("Family-calibrated", C_BLUE)}
MARK = {"SCP": "o", "CV+": "s", "CQR": "^", "WCP": "D", "GP": "o", "RF-z": "s", "Ens-z": "^", "GSCP": "o", "FCP": "s",
        "FCP-W": "D"}


def _style():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                         "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID,
                         "grid.linewidth": 0.5, "axes.spines.top": False, "axes.spines.right": False,
                         "savefig.dpi": 300, "legend.frameon": False, "axes.titlesize": 8.5})


def _save(fig, out, name):
    (out / "figures").mkdir(exist_ok=True)
    fig.savefig(out / "figures" / f"{name}.png", bbox_inches="tight")
    fig.savefig(out / "figures" / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def _md(df, path, floatfmt=3):
    def f(v):
        if isinstance(v, (float, np.floating)):
            return "inf" if np.isinf(v) else ("" if np.isnan(v) else f"{v:.{floatfmt}f}")
        return str(v)
    lines = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(f(v) for v in row) + " |" for row in df.itertuples(index=False)]
    Path(path).write_text("\n".join(lines) + "\n")


def _pm(m, s, d=3):
    return f"{m:.{d}f} ± {s:.{d}f}" if np.isfinite(m) else "inf"


# --------------------------------------------------------------------------------------------- tables
def cell_means(df, alpha=0.1):
    d = df[df.alpha == alpha]
    g = d.groupby(["task", "protocol", "method"])
    agg = g.agg(coverage=("coverage", "mean"), coverage_sd=("coverage", "std"), family_coverage=("family_coverage", "mean"),
                width_sd=("width_sd", "mean"), width_sd_sd=("width_sd", "std"), median_width_sd=("median_width_sd", "mean"),
                inf_rate=("inf_rate", "mean"), interval_score_sd=("interval_score_sd", "mean"),
                interval_score_sd_sd=("interval_score_sd", "std"), undercovered_fams=("undercovered_fams", "mean"),
                cov_novelty_low=("cov_novelty_low", "mean"), cov_novelty_mid=("cov_novelty_mid", "mean"),
                cov_novelty_high=("cov_novelty_high", "mean"), n_seeds=("seed", "nunique"),
                fit_time=("fit_time_s_per_fold", "mean"), r2=("point_r2", "mean"), mae=("point_mae", "mean")).reset_index()
    return agg


def tables(df, out):
    T_ = out / "tables"; T_.mkdir(exist_ok=True)
    cm = cell_means(df)
    cm.to_csv(T_ / "cell_means_alpha0.1.csv", index=False)
    tasks = [t for t in TASK_LABEL if t in cm.task.unique()]
    # Table: point accuracy of the shared base predictor under each protocol (shift severity)
    pa = df[(df.alpha == 0.1) & (df.method == "FCP")].groupby(["task", "protocol"]).agg(
        r2=("point_r2", "mean"), r2_sd=("point_r2", "std"), mae=("point_mae", "mean")).reset_index()
    rows = []
    for t in tasks:
        r = {"Task": TASK_LABEL[t]}
        for p in PROT_LABEL:
            s = pa[(pa.task == t) & (pa.protocol == p)]
            r[f"R² {p}"] = _pm(s.r2.iloc[0], s.r2_sd.iloc[0]) if len(s) else ""
        rows.append(r)
    pd.DataFrame(rows).to_csv(T_ / "table_point_accuracy.csv", index=False)
    _md(pd.DataFrame(rows), T_ / "table_point_accuracy.md")
    # Main table: coverage (mean ± SD over seeds) and mean width for key methods, alpha = 0.1
    for metric, sdcol, name in [("coverage", "coverage_sd", "coverage"), ("width_sd", "width_sd_sd", "width"),
                                ("interval_score_sd", "interval_score_sd_sd", "interval_score")]:
        rows = []
        for t in tasks:
            for p in PROT_LABEL:
                r = {"Task": TASK_LABEL[t], "Protocol": p}
                for m in KEY:
                    s = cm[(cm.task == t) & (cm.protocol == p) & (cm.method == m)]
                    r[m] = _pm(s[metric].iloc[0], s[sdcol].iloc[0], 2 if metric != "coverage" else 3) if len(s) else ""
                rows.append(r)
        tab = pd.DataFrame(rows)
        tab.to_csv(T_ / f"table_main_{name}.csv", index=False)
        _md(tab, T_ / f"table_main_{name}.md")
    # Summary across tasks per protocol (mean of cell means)
    rows = []
    for p in PROT_LABEL:
        for m in KEY + [x for x in ABLATION if x not in KEY]:
            s = cm[(cm.protocol == p) & (cm.method == m)]
            if not len(s):
                continue
            rows.append({"protocol": p, "method": m, "mean_coverage": s.coverage.mean(), "min_cell_coverage": s.coverage.min(),
                         "cells_below_0.88": int((s.coverage < 0.88).sum()), "n_cells": len(s),
                         "mean_family_coverage": s.family_coverage.mean(),
                         "mean_width_sd": s.width_sd.replace(np.inf, np.nan).mean(), "mean_inf_rate": s.inf_rate.mean(),
                         "mean_interval_score_sd": s.interval_score_sd.mean(),  # inf if any interval is infinite
                         "mean_cov_high_novelty": s.cov_novelty_high.mean(), "mean_cov_low_novelty": s.cov_novelty_low.mean()})
    summ = pd.DataFrame(rows)
    summ.to_csv(T_ / "table_summary_by_protocol.csv", index=False)
    _md(summ, T_ / "table_summary_by_protocol.md")
    abl = summ[summ.method.isin(ABLATION)].copy()
    abl["order"] = abl.method.map({m: i for i, m in enumerate(ABLATION)})
    abl = abl.sort_values(["protocol", "order"]).drop(columns="order")
    abl.to_csv(T_ / "table_ablation.csv", index=False)
    _md(abl, T_ / "table_ablation.md")
    # alpha sweep (secondary)
    al = df.groupby(["protocol", "method", "alpha"]).agg(coverage=("coverage", "mean"),
                                                          width_sd=("width_sd", lambda x: x.replace(np.inf, np.nan).mean())).reset_index()
    al = al[al.method.isin(KEY)]
    al.to_csv(T_ / "table_alpha_sweep.csv", index=False)
    _md(al, T_ / "table_alpha_sweep.md")
    return cm, summ


# ----------------------------------------------------------------------------------------- statistics
def statistics(cm, out):
    res = {"unit_of_analysis": "cell = (task, shift protocol); value = mean over outer-split seeds",
           "alpha_level": 0.1, "tests": {}}
    shift = cm[cm.protocol.isin(["system", "cluster"])]
    piv = {met: shift.pivot_table(index=["task", "protocol"], columns="method", values=met)
           for met in ["coverage", "interval_score_sd", "cov_novelty_high", "family_coverage"]}
    cov = piv["coverage"]
    # H1: random-calibrated methods under-cover under family shift
    h1 = {}
    for m in ["SCP", "CV+", "CQR", "WCP"]:
        if m in cov:
            h1[m] = T.one_sample_wilcoxon(cov[m].values, 0.9, alternative="less")
    res["tests"]["H1_random_calibration_undercovers_under_shift"] = {
        "test": "one-sided one-sample Wilcoxon signed-rank of cell coverage vs 0.90", "results": h1}
    # H2: FCP has smaller coverage shortfall than each baseline (Holm across baselines)
    short = (0.9 - cov).clip(lower=0)
    h2 = {}
    for m in BASELINES:
        if m in short and "FCP" in short:
            h2[m] = T.paired_wilcoxon(short["FCP"].values, short[m].values)
    ph = T.holm([h2[m]["p"] for m in h2])
    for (m, p) in zip(h2, ph):
        h2[m]["p_holm"] = float(p)
    res["tests"]["H2_FCP_vs_baselines_coverage_shortfall"] = {
        "test": "two-sided Wilcoxon signed-rank on paired cell shortfall max(0, 0.9 - coverage); Holm over baselines; "
                "median_diff < 0 favours FCP", "results": h2}
    # H3: interval score (lower is better) FCP vs baselines
    isc = piv["interval_score_sd"]
    h3 = {}
    for m in BASELINES:
        if m in isc and "FCP" in isc:
            h3[m] = T.paired_wilcoxon(isc["FCP"].values, isc[m].values)
    ph = T.holm([h3[m]["p"] for m in h3])
    for (m, p) in zip(h3, ph):
        h3[m]["p_holm"] = float(p)
    res["tests"]["H3_FCP_vs_baselines_interval_score"] = {
        "test": "two-sided Wilcoxon signed-rank on paired cell mean Winkler interval score / SD(y); Holm; "
                "median_diff < 0 favours FCP", "results": h3}
    # H4: ablation — normalisation and grouping effects
    h4 = {}
    for a, b, met in [("FCP", "GCV+", "interval_score_sd"), ("FCP", "GCV+", "cov_novelty_high"),
                      ("GCV+", "CV+", "coverage"), ("FCP", "NCV+", "coverage"), ("FCP-W", "FCP", "family_coverage")]:
        P = piv[met]
        if a in P and b in P:
            h4[f"{a}_vs_{b}_{met}"] = T.paired_wilcoxon(P[a].values, P[b].values)
    res["tests"]["H4_ablation"] = {"test": "two-sided Wilcoxon signed-rank on paired cells (uncorrected; exploratory)",
                                   "results": h4}
    # per-protocol replication of H2 (6 cells each)
    per = {}
    for p in ["system", "cluster"]:
        c = cm[cm.protocol == p].pivot_table(index="task", columns="method", values="coverage")
        sh = (0.9 - c).clip(lower=0)
        per[p] = {m: T.paired_wilcoxon(sh["FCP"].values, sh[m].values) for m in ["SCP", "CV+", "CQR", "WCP", "GSCP"] if m in sh}
    res["tests"]["H2_per_protocol"] = per
    (out / "statistics.json").write_text(json.dumps(res, indent=2, default=float))
    # flat table
    rows = []
    for h, block in res["tests"].items():
        if h == "H2_per_protocol":
            for p, d in block.items():
                for m, r in d.items():
                    rows.append({"hypothesis": f"H2 ({p})", "comparison": f"FCP vs {m}", **r})
            continue
        for m, r in block["results"].items():
            rows.append({"hypothesis": h.split("_")[0], "comparison": m if h.startswith("H4") else
                         (f"FCP vs {m}" if h[:2] in ("H2", "H3") else m), **r})
    st = pd.DataFrame(rows)
    st.to_csv(out / "tables" / "table_statistics.csv", index=False)
    _md(st, out / "tables" / "table_statistics.md", 4)
    return res


# -------------------------------------------------------------------------------------------- figures
def fig_coverage(cm, out):
    tasks = [t for t in TASK_LABEL if t in cm.task.unique()]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.3), sharey=True)
    for ax, p in zip(axes, PROT_LABEL):
        for j, m in enumerate(KEY):
            s = cm[(cm.protocol == p) & (cm.method == m)].set_index("task").reindex(tasks)
            x = j + np.linspace(-0.25, 0.25, len(tasks))
            ax.scatter(x, s.coverage, s=9, color=GROUP[m][1], marker=MARK[m], alpha=0.9, linewidths=0)
            ax.plot([j - 0.3, j + 0.3], [s.coverage.mean()] * 2, color=INK, lw=1.2)
        ax.axhline(0.9, color=C_RED, lw=1, ls="--")
        ax.set_xticks(range(len(KEY))); ax.set_xticklabels(KEY, rotation=60, ha="right")
        ax.set_title(PROT_LABEL[p]); ax.set_ylim(0.3, 1.01)
    axes[0].set_ylabel("Empirical coverage (target 0.90)")
    from matplotlib.lines import Line2D
    h = [Line2D([], [], color=c, marker="o", ls="", ms=4, label=l) for l, c in
         [("Random-calibrated conformal", C_ORANGE), ("Model-based (uncalibrated)", C_VIOLET), ("Family-calibrated", C_BLUE)]]
    h += [Line2D([], [], color=INK, lw=1.2, label="Mean over tasks"), Line2D([], [], color=C_RED, ls="--", label="Nominal 0.90")]
    fig.legend(handles=h, loc="upper center", ncol=3, bbox_to_anchor=(0.5, -0.02), fontsize=7)
    fig.text(0.5, -0.19, "Each marker is one dataset (mean over 10 outer splits). FCP-W under cluster holdout: "
             "intervals infinite whenever fewer than 9 training families (Eq. 10).", ha="center", color=INK2, fontsize=6.5)
    _save(fig, out, "fig3_coverage_by_protocol")


def _repel(ys, min_gap):
    """Greedy 1-D label de-overlap: returns label y positions (same order) at least min_gap apart."""
    order = np.argsort(ys); orig = np.array(ys, float)[order]; pos = orig.copy()
    for i in range(1, len(pos)):
        pos[i] = max(pos[i], pos[i - 1] + min_gap)
    pos -= np.mean(pos - orig)  # re-centre so labels spread both up and down
    out = np.empty_like(pos); out[order] = pos
    return out


def fig_tradeoff(cm, out):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4))
    for ax, p in zip(axes, ["system", "cluster"]):
        s = cm[(cm.protocol == p) & cm.method.isin(KEY)]
        g = s.groupby("method").agg(cv=("coverage", "mean"), w=("width_sd", lambda x: x.replace(np.inf, np.nan).mean()),
                                    inf=("inf_rate", "mean"))
        g = g[(g["inf"] < 0.5) & (g.index != "Ens-z")]  # see footnote
        lo_y, hi_y = (0.82, 0.97) if p == "system" else (0.69, 0.95)
        ly = _repel(g["cv"].values, 0.065 * (hi_y - lo_y))
        for (m, r), yl in zip(g.iterrows(), ly):
            ax.scatter(r["w"], r["cv"], color=GROUP[m][1], marker=MARK[m], s=30, zorder=3,
                       facecolors="white" if r["inf"] > 0 else GROUP[m][1], linewidths=1.2)
            lab = m + (f" ({r['inf'] * 100:.0f}% ∞)" if r["inf"] > 0.001 else "")
            ax.annotate(lab, (r["w"], r["cv"]), xytext=(r["w"] + 0.05 * (g["w"].max() - g["w"].min()), yl),
                        textcoords="data", fontsize=6.5, color=INK2, va="center",
                        arrowprops=dict(arrowstyle="-", color=GRID, lw=0.5))
        ax.axhline(0.9, color=C_RED, lw=1, ls="--")
        ax.set_xlabel("Mean interval width / SD(y) (finite intervals)"); ax.set_title(PROT_LABEL[p])
        ax.set_xlim(g["w"].min() * 0.85, g["w"].max() * 1.45); ax.set_ylim(lo_y, hi_y)
    axes[0].set_ylabel("Mean coverage over datasets")
    fig.text(0.5, -0.04, "Open markers: some intervals infinite. Not shown: FCP-W under cluster holdout (64% infinite) and Ens-z "
             "(coverage 0.48 / 0.45, far below the plotted range; Table 3).",
             ha="center", fontsize=6.5, color=INK2)
    _save(fig, out, "fig4_coverage_width_tradeoff")


def fig_novelty(cm, out):
    meths = ["SCP", "CV+", "WCP", "GSCP", "GCV+", "FCP"]
    cols = [C_ORANGE, C_YELLOW, C_MAGENTA, C_AQUA, C_VIOLET, C_BLUE]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.8), sharey=True)
    for ax, p in zip(axes, PROT_LABEL):
        for m, c in zip(meths, cols):
            s = cm[(cm.protocol == p) & (cm.method == m)]
            v = [s.cov_novelty_low.mean(), s.cov_novelty_mid.mean(), s.cov_novelty_high.mean()]
            ax.plot([0, 1, 2], v, color=c, lw=2, marker="o", ms=4, label=m)
        ax.axhline(0.9, color=C_RED, lw=1, ls="--")
        ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["low", "mid", "high"]); ax.set_xlabel("Novelty tertile of test alloy")
        ax.set_title(PROT_LABEL[p])
    axes[0].set_ylabel("Coverage (mean over datasets)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=6, bbox_to_anchor=(0.5, -0.0), fontsize=7)
    _save(fig, out, "fig5_conditional_coverage_novelty")


def fig_ablation(summ, out):
    s = summ[summ.method.isin(ABLATION) & summ.protocol.isin(["system", "cluster"])]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    for ax, met, lab in [(axes[0], "mean_coverage", "Mean coverage"), (axes[1], "mean_interval_score_sd", "Mean interval score / SD(y)")]:
        for k, (p, c) in enumerate([("system", C_BLUE), ("cluster", C_ORANGE)]):
            v = s[s.protocol == p].set_index("method").reindex(ABLATION)[met]
            yy = np.arange(len(ABLATION)) + (k - 0.5) * 0.38
            fin = np.isfinite(v.values)
            ax.barh(yy[fin], v.values[fin], height=0.36, color=c, label=PROT_LABEL[p])
            for y_, f_ in zip(yy, fin):
                if not f_:
                    ax.text(0.05, y_, "∞ (fewer than 9 training families)", va="center", fontsize=6, color=INK2)
        ax.set_yticks(range(len(ABLATION))); ax.set_yticklabels(ABLATION); ax.invert_yaxis(); ax.set_xlabel(lab)
        if met == "mean_coverage":
            ax.axvline(0.9, color=C_RED, ls="--", lw=1); ax.set_xlim(0.5, 1.0)
    axes[1].set_yticklabels([])
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=2, bbox_to_anchor=(0.55, 0.0), fontsize=7)
    _save(fig, out, "fig6_ablation")


def fig_alpha(df, out):
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6), sharey=True)
    for ax, p in zip(axes, PROT_LABEL):
        for m in ["SCP", "CV+", "CQR", "GSCP", "FCP"]:
            s = df[(df.protocol == p) & (df.method == m)].groupby("alpha").coverage.mean()
            ax.plot(1 - s.index, s.values, marker=MARK[m], color=GROUP[m][1], lw=1.5, ms=4,
                    ls="-" if GROUP[m][1] == C_BLUE else ":", label=m)
        ax.plot([0.78, 0.97], [0.78, 0.97], color=INK2, lw=0.8)
        ax.set_xlabel("Nominal coverage 1 − α"); ax.set_title(PROT_LABEL[p])
    axes[0].set_ylabel("Empirical coverage"); axes[-1].legend(fontsize=6.5, loc="lower right")
    _save(fig, out, "fig11_alpha_calibration")


def fig_datasets(out, cfg):
    from experiments import runner as R
    tasks = [t for t in cfg["tasks"]]
    fig, axes = plt.subplots(2, len(tasks), figsize=(7.2, 3.4), squeeze=False)
    for j, t in enumerate(tasks):
        d = R.load_task(t, cfg)
        axes[0, j].hist(d["y"], bins=30, color=C_BLUE, edgecolor="white", linewidth=0.4)
        axes[0, j].set_title(TASK_LABEL[t], fontsize=7)
        vc = pd.Series(d["fam_system"]).value_counts().values
        axes[1, j].hist(vc, bins=np.unique(np.r_[np.geomspace(1, vc.max() + 1, 12).astype(int), vc.max() + 1]),
                        color=C_ORANGE, edgecolor="white", linewidth=0.4)
        axes[1, j].set_xscale("log")
        axes[0, j].tick_params(labelsize=6); axes[1, j].tick_params(labelsize=6)
    axes[0, 0].set_ylabel("Count (target)"); axes[1, 0].set_ylabel("Systems (count)")
    for j in range(len(tasks)):
        axes[1, j].set_xlabel("rows per system", fontsize=6.5)
    fig.tight_layout()
    _save(fig, out, "fig2_dataset_distributions")


def load_merged(cache, task, prot, seed):
    """Baseline bounds from the default run + v2 CV+ bounds (v1 CV+ entries dropped)."""
    f0 = cache / f"main_{task}_{prot}_{seed}_default.pkl"
    f2 = cache / f"main_{task}_{prot}_{seed}_cvplus_v2.pkl"
    if not (f0.exists() and f2.exists()):
        return None
    from fcp.evaluation.protocol import CV_VARIANTS
    r = pickle.loads(f0.read_bytes()); r2 = pickle.loads(f2.read_bytes())
    for side in ("lo", "hi"):
        r[side] = {k: v for k, v in r[side].items() if k[0] not in CV_VARIANTS}
        r[side].update(r2[side])
    return r


def fig_parity(out, cfg):
    from experiments import runner as R
    r = load_merged(R.CACHE, "mpea_hv", "cluster", 0)
    if r is None:
        return
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2), sharex=True, sharey=True)
    y, mu = r["y"], r["mu"]
    o = np.argsort(y)
    for ax, m, c in [(axes[0], "SCP", C_ORANGE), (axes[1], "FCP", C_BLUE)]:
        lo, hi = r["lo"][(m, 0.1)], r["hi"][(m, 0.1)]
        cov = (y >= lo) & (y <= hi)
        ax.vlines(y[o], lo[o], hi[o], color=c, alpha=0.25, lw=0.8)
        ax.scatter(y[cov], mu[cov], s=5, color=c, linewidths=0, label="covered")
        ax.scatter(y[~cov], mu[~cov], s=9, color=C_RED, marker="x", linewidths=0.8, label="not covered")
        lim = [min(y.min(), mu.min()), max(y.max(), mu.max())]
        ax.plot(lim, lim, color=INK2, lw=0.8)
        ax.set_title(f"{m}  (coverage {cov.mean():.2f})")
        ax.set_xlabel("Measured hardness (HV)")
    axes[0].set_ylabel("Predicted hardness (HV) with 90% interval"); axes[1].legend(loc="upper left", fontsize=6.5)
    fig.suptitle("MPEA hardness, unseen composition clusters (seed 0, α = 0.1)", fontsize=8.5, y=1.02)
    _save(fig, out, "fig7_parity_intervals_mpea_hv")


def error_analysis(out, cfg):
    """Per-family coverage of FCP vs SCP under system holdout; relation to novelty, family size and target extremity."""
    from experiments import runner as R
    rows = []
    for f in sorted(R.CACHE.glob("main_*_system_*_default.pkl")):
        meta = pickle.loads(f.read_bytes())["meta"]
        r = load_merged(R.CACHE, meta["task"], "system", meta["seed"])
        if r is None:
            continue
        t, s = meta["task"], meta["seed"]
        y, fam, nov = r["y"], np.asarray(r["families"]), r["novelty"]
        z = np.abs(y - np.median(y)) / (np.quantile(y, 0.75) - np.quantile(y, 0.25) + 1e-12)
        for m in ["SCP", "CV+", "GSCP", "FCP", "FCP-W"]:
            if (m, 0.1) not in r["lo"]:
                continue
            cov = (y >= r["lo"][(m, 0.1)]) & (y <= r["hi"][(m, 0.1)])
            df = pd.DataFrame({"fam": fam, "cov": cov, "nov": nov, "z": z, "abserr": np.abs(y - r["mu"])})
            g = df.groupby("fam").agg(cov=("cov", "mean"), n=("cov", "size"), nov=("nov", "mean"), z=("z", "mean"),
                                      abserr=("abserr", "mean")).reset_index()
            g["task"], g["seed"], g["method"] = t, s, m
            rows.append(g)
    if not rows:
        return None
    fe = pd.concat(rows)
    fe.to_csv(out / "tables" / "family_level_errors.csv", index=False)
    # aggregate: which families are most often under-covered by FCP (n >= 5)
    sub = fe[(fe.method == "FCP") & (fe.n >= 5)]
    worst = sub.groupby(["task", "fam"]).agg(cov=("cov", "mean"), n=("n", "mean"), nov=("nov", "mean"), z=("z", "mean"),
                                             abserr=("abserr", "mean")).reset_index().sort_values("cov").head(15)
    worst.to_csv(out / "tables" / "table_worst_families_FCP.csv", index=False)
    _md(worst, out / "tables" / "table_worst_families_FCP.md")
    # Spearman correlations of family coverage with novelty / extremity / size
    from scipy.stats import spearmanr
    corr = []
    for m in ["SCP", "FCP"]:
        for t in sub.task.unique():
            s = fe[(fe.method == m) & (fe.n >= 5) & (fe.task == t)]
            if len(s) < 8:
                continue
            for v in ["nov", "z", "n"]:
                rho, p = spearmanr(s["cov"], s[v])
                corr.append({"method": m, "task": t, "variable": v, "spearman_rho": rho, "p": p, "n_family_splits": len(s)})
    pd.DataFrame(corr).to_csv(out / "tables" / "table_error_correlations.csv", index=False)
    _md(pd.DataFrame(corr), out / "tables" / "table_error_correlations.md")
    # figure: family coverage vs target extremity (FCP vs SCP), pooled
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    for ax, v, lab in [(axes[0], "z", "Family mean target extremity |y − median| / IQR"),
                       (axes[1], "nov", "Family mean novelty (kNN distance)")]:
        for m, c in [("SCP", C_ORANGE), ("FCP", C_BLUE)]:
            s = fe[(fe.method == m) & (fe.n >= 5)]
            bins = np.quantile(s[v], np.linspace(0, 1, 7))
            idx = np.clip(np.digitize(s[v], bins[1:-1]), 0, 5)
            mcov = [s["cov"][idx == b].mean() for b in range(6)]
            ax.plot(range(6), mcov, marker="o", color=c, lw=2, ms=4, label=m)
        ax.axhline(0.9, color=C_RED, ls="--", lw=1); ax.set_xlabel(lab + " (sextile)")
    axes[0].set_ylabel("Mean within-family coverage"); axes[0].legend(fontsize=6.5)
    _save(fig, out, "fig9_error_analysis_families")
    return fe


def fig_robust(out):
    p = out / "robustness_results.csv"
    if not p.exists():
        return
    d = pd.read_csv(p)
    d = d[(d.alpha == 0.1) & (d.method != "GP")]  # GP was dropped from this experiment for cost; early cached runs ignored
    g = d.groupby(["condition", "method"]).agg(coverage=("coverage", "mean"),
                                                width=("width_sd", lambda x: x.replace(np.inf, np.nan).mean())).reset_index()
    g.to_csv(out / "tables" / "table_robustness.csv", index=False); _md(g, out / "tables" / "table_robustness.md")
    conds = list(g.condition.unique())
    meths = [m for m in ["SCP", "CV+", "CQR", "WCP", "GP", "RF-z", "GSCP", "GCV+", "FCP", "FCP-W"] if m in g.method.unique()]
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    cols = [C_BLUE, C_ORANGE, C_AQUA]
    for k, c in enumerate(conds):
        v = g[g.condition == c].set_index("method").reindex(meths).coverage
        ax.bar(np.arange(len(meths)) + (k - (len(conds) - 1) / 2) * 0.27, v, width=0.25, color=cols[k % 3], label=c)
    ax.axhline(0.9, color=C_RED, ls="--", lw=1); ax.set_ylim(0.5, 1.0)
    ax.set_xticks(range(len(meths))); ax.set_xticklabels(meths); ax.set_ylabel("Coverage (system holdout, mean of datasets)")
    ax.legend(fontsize=6.5, ncol=3, loc="lower left")
    _save(fig, out, "fig8_robustness")


def fig_sens(out):
    p = out / "sensitivity_results.csv"
    if not p.exists():
        return
    d = pd.read_csv(p); d = d[d.alpha == 0.1]
    g = d.groupby(["parameter", "value", "method"]).agg(coverage=("coverage", "mean"),
                                                         width=("width_sd", "mean"),
                                                         interval_score=("interval_score_sd", "mean")).reset_index()
    g.to_csv(out / "tables" / "table_sensitivity.csv", index=False); _md(g, out / "tables" / "table_sensitivity.md")
    pars = list(g.parameter.unique())
    fig, axes = plt.subplots(1, len(pars), figsize=(7.2, 2.4), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, par in zip(axes, pars):
        for m, c in [("FCP", C_BLUE), ("FCP-W", C_AQUA)]:
            s = g[(g.parameter == par) & (g.method == m)].sort_values("value")
            ax.plot(s.value.astype(str), s.coverage, marker="o", color=c, lw=2, ms=4, label=m)
        ax.axhline(0.9, color=C_RED, ls="--", lw=1); ax.set_title(par)
    axes[0].set_ylabel("Coverage (system holdout)"); axes[0].legend(fontsize=6.5)
    fig.text(0.5, -0.05, "Defaults: K=5, n_members=6, family_frac=0.7, novelty_k=5 (results at defaults in Table 3).",
             ha="center", fontsize=6.5, color=INK2)
    _save(fig, out, "fig10_sensitivity")


def fig_eff(out, cm):
    p = out / "efficiency_results.csv"
    if not p.exists():
        return
    e = pd.read_csv(p)
    _md(e, out / "tables" / "table_efficiency.md")
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6))
    for ax, t in zip(axes, e.task.unique()):
        s = e[e.task == t].sort_values("wall_s")
        ax.barh(s.method, s.wall_s, color=[GROUP.get(m, ("", C_VIOLET))[1] for m in s.method], height=0.6)
        for i, (w, mem) in enumerate(zip(s.wall_s, s.peak_rss_mb)):
            ax.text(w, i, f" {w:.1f} s, {mem:.0f} MB", va="center", fontsize=6.5, color=INK2)
        ax.set_xlabel("Wall time for one outer fold (s, 1 CPU core)"); ax.set_title(TASK_LABEL[t])
        ax.set_xlim(0, s.wall_s.max() * 1.6)
    _save(fig, out, "fig12_efficiency")


def fig_workflow(out):
    fig, ax = plt.subplots(figsize=(7.2, 3.4)); ax.axis("off"); ax.set_xlim(0, 12.2); ax.set_ylim(-0.6, 4.3)
    def box(x, y, w, h, txt, c):
        ax.add_patch(matplotlib.patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.08",
                                                        fc=c, ec="none", alpha=0.16))
        ax.add_patch(matplotlib.patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.08",
                                                        fc="none", ec=INK2, lw=0.6))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=6.3, color=INK, linespacing=1.35)
    def arrow(x0, y0, x1, y1):
        ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=0.8, shrinkA=0, shrinkB=0))
    box(0.0, 3.0, 2.1, 1.1, "Alloy compositions\n+ test/processing\nconditions", C_VIOLET)
    box(0.0, 1.55, 2.1, 1.1, "Magpie descriptors\n+ element fractions", C_VIOLET)
    box(0.0, 0.1, 2.1, 1.1, "Alloy family g\n(chemical system or\ncomposition cluster)", C_VIOLET)
    arrow(1.05, 3.0, 1.05, 2.67); arrow(1.05, 1.55, 1.05, 1.22)
    box(2.6, 2.75, 2.9, 1.35, "Step 1\nfamily-grouped K-fold split\nof the training alloys\n(no family in two folds)", C_BLUE)
    box(2.6, 0.1, 2.9, 2.2, "Step 2  (each fold k)\nfamily-bagged ensemble:\nmean μ_k, spread s_k\nnovelty d_k (kNN distance)\nscale σ_k fitted on family-\nout-of-bag residuals only", C_BLUE)
    arrow(2.1, 2.1, 2.6, 3.4); arrow(2.1, 0.65, 2.6, 1.2); arrow(4.05, 2.75, 4.05, 2.32)
    box(5.85, 2.75, 3.3, 1.35, "Step 3\nscores on held-out families\nS_i = |y_i − μ_k(x_i)| / σ_k(x_i)\nweights w_i = 1 or 1/n_g", C_AQUA)
    box(5.85, 0.1, 3.3, 2.2, "Step 4\nweighted CV+ quantiles\nlower: Q_α{μ_k(x) − S_i σ_k(x)}\nupper: Q_1−α{μ_k(x) + S_i σ_k(x)}\n(+∞ mass w_∞ = 1)", C_AQUA)
    arrow(5.5, 1.2, 5.85, 3.4); arrow(7.5, 2.75, 7.5, 2.32)
    box(9.6, 1.0, 2.55, 2.2, "Prediction interval for\nan alloy from an\nunseen family\n\nFCP  (w_i = 1)\nFCP-W  (w_i = 1/n_g)", C_ORANGE)
    arrow(9.15, 1.2, 9.6, 2.1)
    ax.text(6.1, -0.42, "Evaluation: 5 outer folds hold out whole families (random / system / cluster protocols) × 10 seeds",
            ha="center", fontsize=6.3, color=INK2)
    _save(fig, out, "fig1_workflow")


def iteration_table(df, out):
    """v1 (unclamped scale) vs v2 (clamped) for every run in which both exist (alpha = 0.1)."""
    d = df[df.alpha == 0.1]
    v1 = d[d.method.str.endswith(" (v1)")].copy()
    if v1.empty:
        return
    v1["base"] = v1.method.str.replace(" (v1)", "", regex=False)
    keys = ["task", "protocol", "seed"]
    v2 = d[d.method.isin(v1.base.unique())].rename(columns={"method": "base"})
    m = v1.merge(v2, on=keys + ["base"], suffixes=("_v1", "_v2"))
    rows = []
    for (b, p), g in m.groupby(["base", "protocol"]):
        rows.append({"method": b, "protocol": p, "n_runs": len(g),
                     "coverage_v1": g.coverage_v1.mean(), "coverage_v2": g.coverage_v2.mean(),
                     "mean_width_sd_v1": g.width_sd_v1.mean(), "mean_width_sd_v2": g.width_sd_v2.mean(),
                     "median_width_sd_v1": g.median_width_sd_v1.mean(), "median_width_sd_v2": g.median_width_sd_v2.mean(),
                     "interval_score_v1": g.interval_score_sd_v1.mean(), "interval_score_v2": g.interval_score_sd_v2.mean()})
    t = pd.DataFrame(rows)
    t = t[t.method.isin(["FCP", "FCP-W", "NCV+", "GCV+[novelty]", "GCV+"])]
    t.to_csv(out / "tables" / "table_iteration_v1_v2.csv", index=False)
    _md(t, out / "tables" / "table_iteration_v1_v2.md")


def basemodel_analysis(df_main, out):
    p = out / "basemodel_results.csv"
    if not p.exists():
        return
    b = pd.read_csv(p); b = b[b.alpha == 0.1]
    seeds = sorted(b.seed.unique())
    m = df_main[(df_main.alpha == 0.1) & df_main.seed.isin(seeds) & df_main.method.isin(["FCP", "RF-z", "CV+", "GSCP", "SCP"])].copy()
    m["method"] = m["method"] + " [LGBM]"
    m.loc[m.method == "RF-z [LGBM]", "method"] = "RF-z"
    b["method"] = b["method"] + " [RF]"
    allr = pd.concat([m, b])
    cells = allr.groupby(["task", "protocol", "method"]).agg(coverage=("coverage", "mean"), interval_score_sd=("interval_score_sd", "mean"),
                                                             width_sd=("width_sd", "mean"), r2=("point_r2", "mean")).reset_index()
    summ = cells.groupby(["protocol", "method"]).agg(mean_coverage=("coverage", "mean"), min_cell=("coverage", "min"),
                                                     mean_interval_score_sd=("interval_score_sd", "mean"),
                                                     mean_width_sd=("width_sd", "mean")).reset_index()
    summ.to_csv(out / "tables" / "table_basemodel.csv", index=False); _md(summ, out / "tables" / "table_basemodel.md")
    sh = cells[cells.protocol.isin(["system", "cluster"])]
    res = {}
    for a, c in [("FCP [RF]", "RF-z"), ("FCP [RF]", "FCP [LGBM]"), ("FCP [RF]", "CV+ [RF]")]:
        for met in ["interval_score_sd", "coverage"]:
            P = sh.pivot_table(index=["task", "protocol"], columns="method", values=met)
            if a in P and c in P:
                x = P[a]; y = P[c]
                if met == "coverage":
                    x, y = (0.9 - x).clip(lower=0), (0.9 - y).clip(lower=0)
                res[f"{a} vs {c} ({'shortfall' if met == 'coverage' else met})"] = T.paired_wilcoxon(x.values, y.values)
    (out / "statistics_basemodel.json").write_text(json.dumps(res, indent=2, default=float))
    rows = [{"comparison": k, **v} for k, v in res.items()]
    _md(pd.DataFrame(rows), out / "tables" / "table_basemodel_tests.md", 4)


def randfolds_analysis(df_main, out):
    p = out / "randfolds_results.csv"
    if not p.exists():
        return
    r = pd.read_csv(p); r = r[r.alpha == 0.1]
    m = df_main[(df_main.alpha == 0.1) & (df_main.protocol == "cluster") & df_main.method.isin(r.method.unique())]
    rows = []
    for name, d in [("balanced (main)", m), ("random", r)]:
        c = d.groupby(["task", "method"]).agg(cov=("coverage", "mean"), sd=("coverage", "std"),
                                              isc=("interval_score_sd", "mean")).reset_index()
        for meth, g in c.groupby("method"):
            rows.append({"assignment": name, "method": meth, "mean_coverage": g["cov"].mean(), "min_cell": g["cov"].min(),
                         "mean_seed_sd": g["sd"].mean(), "mean_interval_score_sd": g["isc"].mean()})
    t = pd.DataFrame(rows).sort_values(["method", "assignment"])
    t.to_csv(out / "tables" / "table_randfolds.csv", index=False); _md(t, out / "tables" / "table_randfolds.md")


def screening_analysis(out, cfg):
    """Materials decision case study: under the system (unseen chemical system) protocol, an alloy is 'selected' as a
    high performer if its 90%-interval LOWER bound exceeds tau = upper quartile of the task's property. Reports the
    number selected and the false-discovery proportion (selected alloys whose measured property is below tau)."""
    from experiments import runner as R
    rows = []
    for task in ["mpea_hv", "mpea_ys", "steel_ys", "superhard_k", "supercon_tc"]:
        for seed in cfg["seeds"]:
            r = load_merged(R.CACHE, task, "system", seed)
            if r is None:
                continue
            y = r["y"]; tau = np.quantile(y, 0.75)
            for m in ["SCP", "CV+", "CQR", "GP", "RF-z", "GSCP", "FCP"]:
                if (m, 0.1) not in r["lo"]:
                    continue
                sel = r["lo"][(m, 0.1)] >= tau
                rows.append({"task": task, "seed": seed, "method": m, "tau": tau, "n_selected": int(sel.sum()),
                             "false_discoveries": int((sel & (y < tau)).sum()),
                             "true_high_found": int((sel & (y >= tau)).sum()), "n_true_high": int((y >= tau).sum())})
    if not rows:
        return
    d = pd.DataFrame(rows)
    g = d.groupby(["task", "method"]).agg(n_selected=("n_selected", "mean"), fd=("false_discoveries", "mean"),
                                          found=("true_high_found", "mean"), n_high=("n_true_high", "mean")).reset_index()
    g["fdp"] = g.fd / g.n_selected.replace(0, np.nan)
    g["recall"] = g.found / g.n_high
    g.to_csv(out / "tables" / "table_screening.csv", index=False); _md(g, out / "tables" / "table_screening.md")
    tot = d.groupby("method").agg(sel=("n_selected", "sum"), fd=("false_discoveries", "sum"), found=("true_high_found", "sum"),
                                  high=("n_true_high", "sum")).reset_index()
    tot["fdp"] = tot.fd / tot.sel; tot["recall"] = tot.found / tot.high
    tot.to_csv(out / "tables" / "table_screening_pooled.csv", index=False); _md(tot, out / "tables" / "table_screening_pooled.md")


def run(cfg, out):
    out = Path(out)
    _style()
    (out / "tables").mkdir(exist_ok=True); (out / "figures").mkdir(exist_ok=True)
    df_all = pd.read_csv(out / "raw_results.csv")
    iteration_table(df_all, out)
    df = df_all[~df_all.method.str.endswith(" (v1)")]
    cm, summ = tables(df, out)
    stat = statistics(cm, out)
    metrics = {"n_runs": int(df.groupby(["task", "protocol", "seed"]).ngroups), "tasks": sorted(df.task.unique()),
               "summary_alpha0.1": summ.replace({np.inf: "inf"}).to_dict(orient="records")}
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2, default=float))
    fig_workflow(out); fig_datasets(out, cfg); fig_coverage(cm, out); fig_tradeoff(cm, out); fig_novelty(cm, out)
    fig_ablation(summ, out); fig_alpha(df, out); fig_parity(out, cfg); error_analysis(out, cfg)
    fig_robust(out); fig_sens(out); fig_eff(out, cm)
    basemodel_analysis(df, out)
    randfolds_analysis(df, out)
    screening_analysis(out, cfg)
    for name in ["generalization_results.csv"]:
        p = out / name
        if p.exists():
            g = pd.read_csv(p); g = g[g.alpha == 0.1]
            t = g.groupby(["task", "method"]).agg(coverage=("coverage", "mean"), coverage_sd=("coverage", "std"),
                                                 width=("width_sd", "mean")).reset_index()
            t.to_csv(out / "tables" / "table_generalization.csv", index=False); _md(t, out / "tables" / "table_generalization.md")
    print("analysis complete:", out)
