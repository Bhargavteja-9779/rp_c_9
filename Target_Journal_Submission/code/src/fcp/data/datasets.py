"""Dataset loading and cleaning. Every task returns a DataFrame with columns
['formula', 'y', <extra condition columns>] plus metadata. Cleaning rules are documented inline and in the manuscript."""
import re, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

RAW = Path(__file__).resolve().parents[3] / "data" / "raw"

TASKS = {
    # name: (loader, target description, unit)
    "mpea_hv": ("MPEA Vickers hardness", "HV"),
    "mpea_ys": ("MPEA yield strength", "MPa"),
    "steel_ys": ("Steel yield strength (matbench_steels)", "MPa"),
    "supercon_tc": ("Superconductor critical temperature", "K"),
    "superhard_k": ("Bulk modulus (Brgoch superhard set)", "GPa"),
    "expt_hf": ("Experimental formation enthalpy (Kingsbury)", "eV/atom"),
    # confirmatory tasks (pre-registered in supplementary/confirmatory_plan.md)
    "mpea_uts": ("MPEA ultimate tensile strength", "MPa"),
    "mpea_elong": ("MPEA elongation", "%"),
    "steel_uts": ("Steel tensile strength", "MPa"),
    "superhard_g": ("Shear modulus (Brgoch superhard set)", "GPa"),
    "expt_gap": ("Experimental band gap (Matbench)", "eV"),
}


def _mpea():
    df = pd.read_csv(RAW / "MPEA_dataset.csv")
    df.columns = [c.replace("PROPERTY: ", "") for c in df.columns]
    df = df.rename(columns={"FORMULA": "formula", "Processing method": "processing", "Type of test": "test_type",
                            "Test temperature ($^\\circ$C)": "test_temp_C"})
    df["processing"] = df["processing"].fillna("UNKNOWN")
    return df


def load_task(name: str) -> pd.DataFrame:
    """Return a cleaned DataFrame for a task. Exact-duplicate measurement conditions are aggregated by the median
    target (prevents identical inputs appearing in both training and test folds)."""
    if name == "mpea_hv":
        df = _mpea()
        df = df[df["HV"].notna()].copy()
        df["y"] = df["HV"].astype(float)
        keys = ["formula", "processing"]
        out = df.groupby(keys, as_index=False)["y"].median()
        out["cond_processing"] = out["processing"]
        return out.drop(columns=["processing"])
    if name == "mpea_ys":
        df = _mpea()
        df = df[df["YS (MPa)"].notna() & df["test_type"].isin(["C", "T"]) & df["test_temp_C"].notna()].copy()
        df["y"] = df["YS (MPa)"].astype(float)
        keys = ["formula", "processing", "test_type", "test_temp_C"]
        out = df.groupby(keys, as_index=False)["y"].median()
        out = out.rename(columns={"processing": "cond_processing", "test_type": "cond_test_type",
                                  "test_temp_C": "num_test_temp_C"})
        return out
    if name == "steel_ys":
        from matminer.datasets import load_dataset
        df = load_dataset("matbench_steels", data_home=str(RAW))
        out = pd.DataFrame({"formula": df["composition"].astype(str), "y": df["yield strength"].astype(float)})
        return out.groupby("formula", as_index=False)["y"].median()
    if name == "supercon_tc":
        um = pd.read_csv(zipfile.ZipFile(RAW / "superconductivty+data.zip").open("unique_m.csv"))
        out = pd.DataFrame({"formula": um["material"].astype(str), "y": um["critical_temp"].astype(float)})
        return out.groupby("formula", as_index=False)["y"].median()
    if name == "superhard_k":
        from matminer.datasets import load_dataset
        df = load_dataset("brgoch_superhard_training", data_home=str(RAW))
        df = df[~df["suspect_value"].astype(bool)]
        out = pd.DataFrame({"formula": df["formula"].astype(str), "y": df["bulk_modulus"].astype(float)})
        return out.groupby("formula", as_index=False)["y"].median()
    if name == "expt_hf":
        from matminer.datasets import load_dataset
        df = load_dataset("expt_formation_enthalpy_kingsbury", data_home=str(RAW))
        out = pd.DataFrame({"formula": df["formula"].astype(str), "y": df["expt_form_e"].astype(float)})
        return out.groupby("formula", as_index=False)["y"].median()
    if name in ("mpea_uts", "mpea_elong"):
        col = {"mpea_uts": "UTS (MPa)", "mpea_elong": "Elongation (%)"}[name]
        df = _mpea()
        df = df[df[col].notna() & df["test_type"].isin(["C", "T"]) & df["test_temp_C"].notna()].copy()
        df["y"] = df[col].astype(float)
        keys = ["formula", "processing", "test_type", "test_temp_C"]
        out = df.groupby(keys, as_index=False)["y"].median()
        return out.rename(columns={"processing": "cond_processing", "test_type": "cond_test_type",
                                   "test_temp_C": "num_test_temp_C"})
    if name == "steel_uts":
        from matminer.datasets import load_dataset
        df = load_dataset("steel_strength", data_home=str(RAW))
        out = pd.DataFrame({"formula": df["formula"].astype(str), "y": df["tensile strength"].astype(float)})
        return out.groupby("formula", as_index=False)["y"].median()
    if name == "superhard_g":
        from matminer.datasets import load_dataset
        df = load_dataset("brgoch_superhard_training", data_home=str(RAW))
        df = df[~df["suspect_value"].astype(bool)]
        out = pd.DataFrame({"formula": df["formula"].astype(str), "y": df["shear_modulus"].astype(float)})
        return out.groupby("formula", as_index=False)["y"].median()
    if name == "expt_gap":
        from matminer.datasets import load_dataset
        df = load_dataset("matbench_expt_gap", data_home=str(RAW))
        out = pd.DataFrame({"formula": df["composition"].astype(str), "y": df["gap expt"].astype(float)})
        return out.groupby("formula", as_index=False)["y"].median()
    raise KeyError(name)


def load_years(name):
    """Earliest publication year of each cleaned MPEA row (same grouping keys and order as load_task)."""
    df = _mpea()
    df["year"] = df["REFERENCE: year"].astype(float)
    if name == "mpea_hv":
        df = df[df["HV"].notna()]
        return df.groupby(["formula", "processing"], as_index=False)["year"].min()["year"].to_numpy()
    if name == "mpea_ys":
        df = df[df["YS (MPa)"].notna() & df["test_type"].isin(["C", "T"]) & df["test_temp_C"].notna()]
        return df.groupby(["formula", "processing", "test_type", "test_temp_C"], as_index=False)["year"].min()["year"].to_numpy()
    if name in ("mpea_uts", "mpea_elong"):
        col = {"mpea_uts": "UTS (MPa)", "mpea_elong": "Elongation (%)"}[name]
        df = df[df[col].notna() & df["test_type"].isin(["C", "T"]) & df["test_temp_C"].notna()]
        return df.groupby(["formula", "processing", "test_type", "test_temp_C"], as_index=False)["year"].min()["year"].to_numpy()
    raise KeyError(name)
