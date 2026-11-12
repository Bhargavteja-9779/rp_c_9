"""Audit: compositions that occur under more than one formula spelling (e.g. YBa2Cu3O7 vs Ba2Cu3O7Y). These cannot leak
across folds in the system/cluster protocols (same family), but can in the random protocol, whose rows are grouped by
formula string. Reports counts per task and the random-protocol coverage with the affected rows excluded."""
import sys, yaml
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT))
from pymatgen.core import Composition
from experiments import runner as R, analysis as A


def canon(f):
    return tuple(sorted((e.symbol, round(v, 4)) for e, v in Composition(f).fractional_composition.items()))


def main():
    cfg = yaml.safe_load(open(ROOT / "config" / "default.yaml"))
    out = []
    for t in cfg["tasks"]:
        d = R.load_task(t, cfg)
        df = pd.DataFrame({"f": d["formula"], "c": [canon(f) for f in d["formula"]]})
        n_spell = df.groupby("c").f.transform("nunique")
        dup = (n_spell > 1).values  # composition written with more than one distinct formula string
        row = {"task": t, "rows": len(df), "rows_with_alt_spelling": int(dup.sum())}
        if dup.any():
            for m in ["SCP", "CV+", "FCP"]:
                cv_all, cv_ex = [], []
                for s in cfg["seeds"]:
                    r = A.load_merged(R.CACHE, t, "random", s)
                    y = r["y"]; cov = (y >= r["lo"][(m, 0.1)]) & (y <= r["hi"][(m, 0.1)])
                    cv_all.append(cov.mean()); cv_ex.append(cov[~dup].mean())
                row[f"{m}_random_cov_all"] = sum(cv_all) / len(cv_all)
                row[f"{m}_random_cov_excl"] = sum(cv_ex) / len(cv_ex)
        out.append(row)
    df = pd.DataFrame(out)
    df.to_csv(ROOT / "results" / "tables" / "table_duplicate_spelling_audit.csv", index=False)
    print(df.round(3).to_string())


if __name__ == "__main__":
    main()
