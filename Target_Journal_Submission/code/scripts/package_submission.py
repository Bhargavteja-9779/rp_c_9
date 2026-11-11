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
    print("packaged:", sorted(x.name for x in (ROOT / "results").iterdir()))


if __name__ == "__main__":
    main()
