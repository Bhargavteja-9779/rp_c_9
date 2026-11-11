"""Composition featurization and alloy-family definitions.

Features: 132 Magpie elemental-property statistics (Ward et al., npj Comput. Mater. 2, 16028 (2016)) computed with
matminer, plus atomic fractions of every element that occurs in the task, plus measurement-condition columns
(one-hot for `cond_*`, numeric for `num_*`). No feature uses the target, so there is no target leakage.

Families:
  F1 'system'  : set of elements with atomic fraction >= 0.01 (the alloy/chemical system; trace elements ignored)
  F2 'cluster' : k-means (k=10, fixed seed) on atomic-fraction vectors (leave-one-cluster-out style, Meredig et al. 2018)
"""
import pickle, warnings
from pathlib import Path
import numpy as np
import pandas as pd

PROC = Path(__file__).resolve().parents[3] / "data" / "processed"
FAMILY_THRESHOLD = 0.01


def _compositions(formulas):
    from pymatgen.core import Composition
    comps, ok = [], []
    for f in formulas:
        try:
            c = Composition(f)
            if c.num_atoms <= 0:
                raise ValueError
            comps.append(c); ok.append(True)
        except Exception:
            comps.append(None); ok.append(False)
    return comps, np.array(ok)


def featurize(df: pd.DataFrame):
    from matminer.featurizers.composition import ElementProperty
    comps, ok = _compositions(df["formula"])
    n_bad = int((~ok).sum())
    df = df.loc[ok].reset_index(drop=True)
    comps = [c for c, k in zip(comps, ok) if k]
    ep = ElementProperty.from_preset("magpie", impute_nan=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mag = np.array([ep.featurize(c) for c in comps], dtype=float)
    mag_cols = ["magpie_" + c for c in ep.feature_labels()]
    elements = sorted({e.symbol for c in comps for e in c.elements})
    frac = np.zeros((len(comps), len(elements)))
    idx = {e: i for i, e in enumerate(elements)}
    for r, c in enumerate(comps):
        fc = c.fractional_composition
        for e, v in fc.items():
            frac[r, idx[e.symbol]] = v
    X = pd.DataFrame(mag, columns=mag_cols)
    F = pd.DataFrame(frac, columns=["frac_" + e for e in elements])
    parts = [X, F]
    for c in df.columns:
        if c.startswith("cond_"):
            parts.append(pd.get_dummies(df[c].astype(str), prefix=c).astype(float))
        elif c.startswith("num_"):
            parts.append(df[[c]].astype(float))
    feats = pd.concat(parts, axis=1)
    feats = feats.loc[:, feats.std(axis=0) > 0]  # drop constant columns (no information, determined without target)
    systems = ["-".join(sorted(e for e, v in zip(elements, row) if v >= FAMILY_THRESHOLD)) for row in frac]
    return df, feats, frac, elements, systems, n_bad


def cluster_families(frac, k=10, seed=0):
    from sklearn.cluster import KMeans
    km = KMeans(n_clusters=k, n_init=10, random_state=seed).fit(frac)
    return np.array([f"C{c}" for c in km.labels_])


def build_task(name, k_clusters=10, force=False):
    """Load, featurize and cache a task. Returns dict with X (float32 array), y, families, metadata."""
    from fcp.data.datasets import load_task
    PROC.mkdir(parents=True, exist_ok=True)
    cache = PROC / f"{name}.pkl"
    if cache.exists() and not force:
        return pickle.loads(cache.read_bytes())
    raw = load_task(name)
    n_raw = len(raw)
    df, feats, frac, elements, systems, n_bad = featurize(raw)
    obj = {
        "name": name,
        "X": feats.to_numpy(dtype=np.float32),
        "feature_names": list(feats.columns),
        "y": df["y"].to_numpy(dtype=float),
        "formula": df["formula"].astype(str).to_numpy(),
        "fam_system": np.array(systems),
        "fam_cluster": cluster_families(frac, k=k_clusters),
        "frac": frac.astype(np.float32),
        "elements": elements,
        "n_after_dedup": n_raw,
        "n_unparseable": n_bad,
        "conditions": {c: df[c].to_numpy() for c in df.columns if c.startswith(("cond_", "num_"))},
    }
    cache.write_bytes(pickle.dumps(obj))
    return obj
