"""Assemble the journal submission package (no code: code is available on request)."""
import json, re, shutil, sys, zipfile
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MS = ROOT / "manuscript"
OUT = ROOT / "submission_package"
ZIP = ROOT / "JMRT_submission_package.zip"


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "Figures").mkdir(parents=True)
    files = {
        "01_Cover_letter.docx": MS / "cover_letter.docx",
        "02_Title_page.docx": MS / "Title_page.docx",
        "03_Manuscript.docx": MS / "Final_Manuscript.docx",
        "03_Manuscript.pdf": MS / "Final_Manuscript.pdf",
        "04_Highlights.docx": MS / "highlights.docx",
        "05_Graphical_abstract.png": MS / "graphical_abstract.png",
        "06_Supplementary_Material.docx": ROOT / "supplementary" / "Supplementary_Material.docx",
        "07_Declaration_of_interests.docx": MS / "Declaration_of_interests.docx",
    }
    for dst, src in files.items():
        shutil.copy2(src, OUT / dst)
    # figures in manuscript order: vector PDF + 300-dpi TIFF (Elsevier artwork formats)
    rows = []
    for spec, prefix in [("spec.json", "Fig"), ("supp_spec.json", "Fig_S")]:
        for b in json.load(open(HERE / spec))["blocks"]:
            if b["type"] != "figure":
                continue
            cap = "".join(r.get("t", "") for r in b.get("caption", []))
            m = re.match(r"Fig\. (S?\d+)\.", cap)
            if not m:
                continue
            name = f"{prefix}{m.group(1).lstrip('S')}"
            src = Path(b["path"])
            if src.with_suffix(".pdf").exists():
                shutil.copy2(src.with_suffix(".pdf"), OUT / "Figures" / f"{name}.pdf")
            im = Image.open(src)
            if im.mode in ("RGBA", "P", "LA"):
                bg = Image.new("RGB", im.size, "white")
                bg.paste(im.convert("RGBA"), mask=im.convert("RGBA").split()[-1])
                im = bg
            im.save(OUT / "Figures" / f"{name}.tif", dpi=(300, 300), compression="tiff_lzw")
            rows.append(f"  {name}: {cap[:90]}...")
    (OUT / "00_README_submission.txt").write_text(
        "Submission package — Journal of Materials Research and Technology (Elsevier)\n"
        "Authors: P N Bhargav Teja (first author); Ragavan K (corresponding author)\n\n"
        "Upload order in Editorial Manager:\n"
        "  01 Cover letter; 02 Title page (author details); 03 Manuscript (Word; PDF for checking); 04 Highlights;\n"
        "  05 Graphical abstract; Figures/ (TIFF 300 dpi, PDF vector); 06 Supplementary material;\n"
        "  07 Declaration of interests (or regenerate it with Elsevier's online declaration tool).\n\n"
        "Before submitting, fill in the placeholders:\n"
        "  - affiliation [Department, Institution, City, Postal code, Country]\n"
        "  - corresponding-author e-mail of Ragavan K\n"
        "  - date in the cover letter\n"
        "  (in 01, 02 and 03; search for '[').\n\n"
        "Code: not included; available from the corresponding author on request (as stated in the manuscript).\n\n"
        "Figures:\n" + "\n".join(rows) + "\n")
    if ZIP.exists():
        ZIP.unlink()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                z.write(p, Path("JMRT_submission") / p.relative_to(OUT))
    print(ZIP, round(ZIP.stat().st_size / 1e6, 1), "MB;", sum(1 for _ in OUT.rglob("*") if _.is_file()), "files")


if __name__ == "__main__":
    main()
