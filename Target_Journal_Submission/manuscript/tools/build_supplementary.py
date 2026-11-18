"""Supplementary Material (DOCX spec) generated from machine-readable result tables."""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from mdocx import runs
import build_manuscript as B

TAB = B.TAB


def fmt(v, d=3):
    if isinstance(v, (float, np.floating)):
        return "∞" if np.isinf(v) else ("" if np.isnan(v) else f"{v:.{d}f}")
    return str(v)


def table_block(caption, df, cols=None, d=3, widths=None, fs=14):
    cols = cols or list(df.columns)
    rows = [[fmt(r[c], d) for c in cols] for _, r in df.iterrows()]
    w = widths or [1 / len(cols)] * len(cols)
    return {"type": "table", "caption": runs(caption), "header": cols, "rows": rows, "col_widths": w, "font_size": fs}


def main():
    V = B.load(); B.build(V)
    F = {k: i + 1 for i, k in enumerate(B.NUMBERING["fig"])}
    blocks = [{"type": "title", "text": "Supplementary Material"},
              {"type": "center", "runs": runs("for: " + B.TITLE)},
              {"type": "para", "runs": runs("All tables are generated automatically from the result files of the study. Notation and protocols are as in the "
                                            "main text.")}]
    n = 0

    def add(cap, df, **kw):
        nonlocal n
        n += 1
        blocks.append(table_block(f"**Table S{n}.** " + cap, df, **kw))

    def render_md(path, heading, preface=None):
        """Minimal Markdown renderer: '## ' headings, '- ' bullets, numbered items, indented continuations, pipe tables."""
        import re as _re
        blocks.append({"type": "heading", "level": 1, "text": heading})
        if preface:
            blocks.append({"type": "para", "runs": runs(preface)})
        lines = path.read_text().replace("`", "").split("\n")[1:]
        para, bullets, table = [], [], []

        def flush():
            if para:
                blocks.append({"type": "para", "runs": runs(" ".join(para))}); para.clear()
            if bullets:
                blocks.append({"type": "bullets", "items": [runs(x) for x in bullets]}); bullets.clear()
            if table:
                hdr = [c.strip() for c in table[0].strip("|").split("|")]
                rows = [[c.strip().replace("\\|", "|").replace("**", "") for c in _re.split(r"(?<!\\)\|", r.strip().strip("|"))] for r in table[2:]]
                blocks.append({"type": "table", "caption": runs(""), "header": hdr, "rows": rows,
                               "col_widths": [1 / len(hdr)] * len(hdr), "font_size": 14})
                table.clear()
        for line in lines:
            st = line.strip()
            if st.startswith("|"):
                if para or bullets:
                    f_t = table[:]; table.clear(); flush(); table.extend(f_t)
                table.append(st); continue
            if table:
                flush()
            if line.startswith("## "):
                flush(); blocks.append({"type": "heading", "level": 2, "text": line[3:]})
            elif not st:
                flush()
            elif _re.match(r"^\s*- ", line):
                if para:
                    blocks.append({"type": "para", "runs": runs(" ".join(para))}); para.clear()
                bullets.append(st[2:])
            elif _re.match(r"^\d+\. ", st):
                flush(); para.append(st)
            elif line.startswith("   ") and (bullets or para):
                (bullets if bullets else para)[-1] += " " + st
            else:
                if bullets:
                    blocks.append({"type": "bullets", "items": [runs(x) for x in bullets]}); bullets.clear()
                para.append(st)
        flush()

    SUP = HERE.parents[1] / "supplementary"
    render_md(SUP / "theory_note.md", "Supplementary Note S1. Family-level finite-sample guarantee")
    render_md(SUP / "confirmatory_plan.md", "Supplementary Note S2. Pre-registered confirmatory plan (verbatim)",
              "The plan below is reproduced verbatim from the file committed to the project's version-control history on "
              "2026-11-13 at 12:03:31 UTC; the first confirmatory run started at 12:04 UTC and its first result was written at "
              "12:06:02 UTC. The version-control history is available from the corresponding author on request.")
    # Supplementary figures (numbering shared with the manuscript: B.SUPP_FIGS)
    blocks.append({"type": "heading", "level": 1, "text": "Supplementary figures"})
    for i, (key, fname, cap) in enumerate(B.SUPP_FIGS):
        fb = B.fig_block(fname, f"**Fig. S{i + 1}.** " + cap)
        blocks.append(fb)
    blocks.append({"type": "heading", "level": 1, "text": "Supplementary tables"})
    it = pd.read_csv(TAB / "table_iteration_v1_v2.csv")
    add("Scale-model revision (Section 8): v1 (unclamped) vs v2 (inputs clamped to their fitting range), three alloy tasks, 10 "
        "seeds, α = 0.1.", it, d=3)
    for metric, name in [("coverage", "coverage (mean ± SD over 10 seeds)"), ("width", "mean finite interval width / SD(y)"),
                         ("interval_score", "mean interval score / SD(y)")]:
        t = pd.read_csv(TAB / f"table_main_{metric}.csv")
        add(f"Per-dataset {name} at α = 0.1 for all key methods and protocols.", t, fs=11,
            widths=[0.13, 0.07] + [0.08] * 10)
    al = pd.read_csv(TAB / "table_alpha_sweep.csv")
    add("Coverage and mean width at α ∈ {0.05, 0.1, 0.2} (mean over datasets).", al)
    for f, cap in [("table_robustness.csv", "Robustness (Section 9.1): coverage and width under label noise and reduced training families."),
                   ("table_generalization.csv", "Mis-specified family definition (Section 9.2): calibration on chemical systems, test on unseen composition clusters (5 seeds)."),
                   ("table_temporal.csv", "Chronological test (Section 9.3)."),
                   ("table_sensitivity.csv", "Sensitivity of FCP / FCP-W to K, M, φ and k_nn (Section 9.7)."),
                   ("table_basemodel.csv", "Base-learner swap (Section 9.4): methods with random-forest members vs LightGBM members and RF-z (seeds 0–4)."),
                   ("table_randfolds.csv", "Cluster protocol with balanced vs fully random assignment of clusters to outer folds (Section 9.7)."),
                   ("table_mondrian.csv", "Mondrian split conformal prediction on novelty tertiles (Section 9.7)."),
                   ("table_screening.csv", "Screening for high performers (Section 7.5), per task."),
                   ("table_metallurgy.csv", "Coverage and width by metallurgical descriptor (alloy class, phase, VEC regime, δ tertile) for MPEA tasks (Section 7.6)."),
                   ("table_confirm_summary.csv", "Pre-registered confirmatory study: summary over the five new tasks (Section 9.5)."),
                   ("table_confirm_cells.csv", "Pre-registered confirmatory study: per task and protocol."),
                   ("table_confirm_temporal.csv", "Confirmatory chronological test for MPEA tensile strength and elongation."),
                   ("table_familydef.csv", "Sensitivity to the family definition (Section 9.6): chemical-system threshold (unseen-system protocol; MPEA, steel and superconductor tasks) and number of composition clusters (unseen-cluster protocol; all six tasks), seeds 0–4. Default settings (1 at.%, k = 10) from the main run with the same seeds."),
                   ("table_fcps.csv", "Empirical check of Proposition 1 (Section 9.7): family-subsampled FCP-S vs FCP-W and FCP under unseen-system holdout, with the finite-sample bound evaluated at the number of training families G (10 seeds)."),
                   ("table_worst_families_FCP.csv", "Families with the lowest FCP coverage under unseen-system holdout (≥ 5 alloys; means over seeds)."),
                   ("efficiency_results.csv", "Isolated-process wall time and peak memory for one outer fold (Section 10)."),
                   ("table_error_correlations.csv", "Spearman correlation of within-family coverage with novelty (nov), target extremity (z) and family size (n), system protocol."),
                   ("table_statistics.csv", "All hypothesis tests (statistics.json in tabular form).")]:
        p = TAB / f
        if p.exists():
            d = pd.read_csv(p)
            d = d.drop(columns=[c for c in ["statistic"] if c in d.columns])
            add(cap, d, fs=10)
    blocks.append({"type": "heading", "level": 1, "text": "S. Notes on figure types"})
    blocks.append({"type": "para", "runs": runs(
        "The study concerns regression intervals, so classification diagnostics (confusion matrices, ROC and PR curves) do not "
        f"apply. Their roles are taken by coverage-versus-nominal plots (Fig. S{1 + [k for k, _, _ in B.SUPP_FIGS].index('alpha')}), "
        f"conditional coverage by novelty (main-text Fig. {F['novelty']}), parity plots with intervals (Fig. S{1 + [k for k, _, _ in B.SUPP_FIGS].index('parity')}) "
        f"and per-family error analysis (main-text Fig. {F['errors']}). Tree ensembles are not trained iteratively "
        "with a validation loss, so training curves are not shown. Hyper-parameter sensitivity is reported instead (Fig. S2).")})
    spec = {"meta": {"title": "Supplementary Material", "line_numbers": False}, "blocks": blocks}
    (HERE / "supp_spec.json").write_text(json.dumps(spec, ensure_ascii=False))
    print("supplementary tables:", n)


if __name__ == "__main__":
    main()
