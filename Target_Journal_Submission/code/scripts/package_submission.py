"""Assemble the submission package layout from generated outputs (run after `run_all.py --mode full`).

Target_Journal_Submission/
  results/   raw_results.csv, metrics.json, statistics.json, *_results.csv, experiment_logs/
  figures/   every figure (PNG 300 dpi + PDF)
  tables/    every table (CSV + Markdown)
Nothing is computed here; files are copied verbatim so that the package mirrors code/results exactly.
"""
import shutil
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
ROOT = CODE.parent
RES = CODE / "results"


def main():
    (ROOT / "results" / "experiment_logs").mkdir(parents=True, exist_ok=True)
    for p in RES.glob("*.csv"):
        shutil.copy2(p, ROOT / "results" / p.name)
    for p in RES.glob("*.json"):
        shutil.copy2(p, ROOT / "results" / p.name)
    for p in (RES / "logs").glob("*"):
        shutil.copy2(p, ROOT / "results" / "experiment_logs" / p.name)
    for sub in ["figures", "tables"]:
        dst = ROOT / sub
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(RES / sub, dst)
    figure_map()
    print("packaged:", sorted(x.name for x in (ROOT / "results").iterdir()))


def figure_map():
    """Copy figures under their manuscript numbers (figures/for_submission/) and write FIGURE_MAP.md, because the
    file names of analysis.py (fig1..fig13) predate the final figure order of the manuscript."""
    import json, re
    tools = ROOT / "manuscript" / "tools"
    out = ROOT / "figures" / "for_submission"
    out.mkdir(parents=True, exist_ok=True)
    rows = ["| Manuscript figure | Source file (code/results/figures) | Submission file |", "|---|---|---|"]
    for spec, prefix in [("spec.json", "Fig"), ("supp_spec.json", "Fig_S")]:
        sp = tools / spec
        if not sp.exists():
            continue
        for b in json.load(open(sp))["blocks"]:
            if b["type"] != "figure":
                continue
            cap = "".join(r.get("t", "") for r in b.get("caption", []))
            m = re.match(r"Fig\. (S?\d+)\.", cap)
            if not m:
                continue
            num = m.group(1).lstrip("S")
            src = Path(b["path"])
            for ext in (".png", ".pdf"):
                f = src.with_suffix(ext)
                if f.exists():
                    shutil.copy2(f, out / f"{prefix}{num}{ext}")
            rows.append(f"| Fig. {m.group(1)} | {src.stem} | {prefix}{num}.png / .pdf |")
    ga = RES / "figures" / "graphical_abstract.png"
    if ga.exists():
        shutil.copy2(ga, out / "Graphical_abstract.png")
    (ROOT / "figures" / "FIGURE_MAP.md").write_text("# Figure numbering map\n\n" + "\n".join(rows) + "\n")


if __name__ == "__main__":
    main()
