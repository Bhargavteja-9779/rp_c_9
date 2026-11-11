"""Download the six public datasets used in the study into data/raw/.
Sources (all public):
  - MPEA dataset (Borg et al., Sci. Data 7, 430 (2020)): GitHub CitrineInformatics/MPEA_dataset
  - SuperCon-derived superconductivity data (Hamidieh, Comput. Mater. Sci. 154, 346 (2018)): UCI ML repository id 464
  - matbench_steels (Dunn et al., npj Comput. Mater. 6, 138 (2020)), brgoch_superhard_training (Mansouri Tehrani et al.,
    JACS 140, 9844 (2018)) and expt_formation_enthalpy_kingsbury (Kingsbury et al., 2022), all via matminer.datasets.
"""
import os, sys, hashlib, urllib.request
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
URLS = {
    "MPEA_dataset.csv": "https://raw.githubusercontent.com/CitrineInformatics/MPEA_dataset/master/MPEA_dataset.csv",
    "superconductivty+data.zip": "https://archive.ics.uci.edu/static/public/464/superconductivty+data.zip",
}
MATMINER = ["matbench_steels", "brgoch_superhard_training", "expt_formation_enthalpy_kingsbury"]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for name, url in URLS.items():
        dst = RAW / name
        if not dst.exists() or dst.stat().st_size == 0:
            print("downloading", url)
            urllib.request.urlretrieve(url, dst)
    from matminer.datasets import load_dataset
    for n in MATMINER:
        load_dataset(n, data_home=str(RAW))
    with open(RAW / "SHA256SUMS.txt", "w") as f:
        for p in sorted(RAW.iterdir()):
            if p.is_file() and p.name != "SHA256SUMS.txt" and p.stat().st_size > 0:
                f.write(f"{sha256(p)}  {p.name}\n")
    print((RAW / "SHA256SUMS.txt").read_text())


if __name__ == "__main__":
    sys.exit(main())
