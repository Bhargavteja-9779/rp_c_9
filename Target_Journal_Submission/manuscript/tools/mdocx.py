"""Small helpers to author the manuscript spec: inline markup -> runs, citations -> numbered references.

Inline markup:  **bold**  *italic*  _{subscript}  ^{superscript}   citations: [@key] or [@key1;@key2]
"""
import csv, json, re
from pathlib import Path

SUPP = Path(__file__).resolve().parents[2] / "supplementary"

TOKEN = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*|_\{[^}]*\}|\^\{[^}]*\})")


def runs(text):
    out = []
    for part in TOKEN.split(text):
        if not part:
            continue
        if part.startswith("**"):
            out.append({"t": part[2:-2], "b": True})
        elif part.startswith("*"):
            out.append({"t": part[1:-1], "i": True})
        elif part.startswith("_{"):
            out.append({"t": part[2:-1], "sub": True})
        elif part.startswith("^{"):
            out.append({"t": part[2:-1], "sup": True})
        else:
            out.append({"t": part})
    return out


class Bib:
    """Numbered citations in order of first appearance; entries built from the Crossref/arXiv audit files."""

    def __init__(self, entries):
        self.entries = entries  # key -> dict
        self.order = []

    def cite(self, text):
        def rep(m):
            keys = [k.strip().lstrip("@") for k in m.group(1).split(";")]
            nums = []
            for k in keys:
                if k not in self.entries:
                    raise KeyError(f"unknown citation key {k}")
                if k not in self.order:
                    self.order.append(k)
                nums.append(self.order.index(k) + 1)
            nums = sorted(set(nums))
            # compress ranges 3,4,5 -> 3–5
            parts, i = [], 0
            while i < len(nums):
                j = i
                while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
                    j += 1
                parts.append(f"{nums[i]}–{nums[j]}" if j - i >= 2 else ",".join(str(n) for n in nums[i:j + 1]))
                i = j + 1
            return "[" + ",".join(parts) + "]"
        return re.sub(r"\[(@[^\]]+)\]", rep, text)

    def formatted(self):
        return [self.entries[k]["formatted"] for k in self.order]


def _initials(given):
    parts = re.split(r"[\s]+", given.strip())
    out = []
    for p in parts:
        if not p:
            continue
        sub = p.split("-")
        out.append("-".join(s[0] + "." for s in sub if s))
    return " ".join(out)


def _authors(auth_str):
    names = []
    for a in [x.strip() for x in auth_str.split(";") if x.strip()]:
        if "," in a:
            fam, giv = a.split(",", 1)
            names.append(f"{_initials(giv)} {fam.strip()}".strip())
        else:
            names.append(a)
    return ", ".join(names)


def load_bib(keymap, manual):
    """keymap: key -> DOI (resolved through references_verified.csv); manual: key -> formatted string (arXiv /
    proceedings verified separately)."""
    rows = {r["doi"].lower(): r for r in csv.DictReader(open(SUPP / "references_verified.csv"))}
    entries = {}
    for k, doi in keymap.items():
        r = rows[doi.lower()]
        assert r["status"] == "verified", (k, doi, r["status"])
        auth = _authors(r["authors"]) if r["authors"] else ""
        title = re.sub(r"\s+", " ", r["title"]).strip()
        venue = re.sub(r"\s+", " ", r["venue"]).replace("&amp;", "&").strip()
        vol = r["volume"].split(".")[0] if r["volume"] else ""
        page = r["page"]
        yr = r["year"].split(".")[0]
        if r["type"] in ("book", "monograph"):
            s = f"{auth + ', ' if auth else ''}{title}, {venue}, {yr}. https://doi.org/{doi}"
        else:
            s = f"{auth}, {title}, {venue}{' ' + vol if vol else ''} ({yr}){' ' + page if page else ''}. https://doi.org/{doi}"
        entries[k] = {"formatted": s, "doi": doi}
    for k, s in manual.items():
        entries[k] = {"formatted": s, "doi": None}
    return entries
