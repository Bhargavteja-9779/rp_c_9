"""Title page and declaration-of-interest documents for the Elsevier submission (author data from build_manuscript)."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_manuscript as B
from mdocx import runs


def main():
    P = lambda t: {"type": "para", "runs": runs(t)}
    authors = ", ".join(f"{n}^{{{a}{',*' if c else ''}}}" for n, a, c in B.AUTHORS)
    title = [{"type": "title", "text": B.TITLE},
             {"type": "center", "runs": runs(authors)},
             {"type": "center", "runs": runs(f"^{{a}} {B.AFFIL}"), "size": 20},
             {"type": "center", "runs": runs(f"^{{*}} Corresponding author: Ragavan K, {B.CORR_EMAIL}"), "size": 20},
             {"type": "heading", "level": 1, "text": "Author details"},
             {"type": "bullets", "items": [
                 runs("**P N Bhargav Teja** (first author): Conceptualization, Methodology, Software, Validation, Formal analysis, "
                      "Investigation, Data curation, Visualization, Writing – original draft, Writing – review & editing."),
                 runs("**Ragavan K** (corresponding author): Supervision.")]},
             {"type": "heading", "level": 1, "text": "Declarations"},
             P("**Funding:** This research did not receive any specific grant from funding agencies in the public, commercial, or "
               "not-for-profit sectors."),
             P("**Competing interests:** The authors declare that they have no known competing financial interests or personal "
               "relationships that could have appeared to influence the work reported in this paper."),
             P("**Data availability:** All datasets are publicly available (links in the manuscript). The code will be made "
               "available from the corresponding author on reasonable request."),
             P("**Keywords:** " + "; ".join(B.KEYWORDS))]
    (HERE / "titlepage_spec.json").write_text(json.dumps({"meta": {"title": "Title page", "line_numbers": False},
                                                          "blocks": title}, ensure_ascii=False))
    doi = [{"type": "title", "text": "Declaration of interests"},
           P(f"Manuscript: \"{B.TITLE}\""),
           P("☒ The authors declare that they have no known competing financial interests or personal relationships that could "
             "have appeared to influence the work reported in this paper."),
           P("☐ The authors declare the following financial interests/personal relationships which may be considered as "
             "potential competing interests: (none)"),
           P("P N Bhargav Teja"), P("Ragavan K (corresponding author)")]
    (HERE / "doi_spec.json").write_text(json.dumps({"meta": {"title": "Declaration of interests", "line_numbers": False},
                                                    "blocks": doi}, ensure_ascii=False))
    print("title page and declaration specs written")


if __name__ == "__main__":
    main()
