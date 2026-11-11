"""Citation audit: resolve every DOI in references.csv against Crossref and record title/authors/year/venue,
so that bibliographic details in the manuscript are taken from the registry, not from memory."""
import csv, json, sys, time, urllib.request, urllib.parse
from pathlib import Path

DOIS = [
 "10.1007/b106715", "10.1080/01621459.2017.1307116", "10.1214/20-AOS1965", "10.1080/01621459.2022.2060112",
 "10.1214/23-AOS2276", "10.1613/jair.3198", "10.1561/2200000101", "10.1038/npjcompumats.2016.28",
 "10.1016/j.commatsci.2018.05.018", "10.1016/j.commatsci.2012.10.028", "10.1038/s41597-020-00768-9",
 "10.1016/j.commatsci.2018.07.052", "10.1038/s41524-020-00406-3", "10.1021/jacs.8b02717", "10.1038/s41524-022-00881-w",
 "10.1039/C8ME00012C", "10.1023/A:1010933404324", "10.1198/016214506000001437", "10.1088/2632-2153/ab7e1a",
 "10.1038/s41524-022-00794-8", "10.1063/5.0133528", "10.1021/acsomega.6c02607", "10.3390/polym18192445",
 "10.1038/s41524-024-01316-4", "10.1007/s40192-017-0098-z", "10.1016/j.actamat.2019.03.010", "10.1126/science.abo4940",
 "10.1038/s41524-019-0153-8", "10.1016/j.actamat.2016.08.081", "10.1016/j.commatsci.2019.109203",
 "10.1021/acs.jcim.0c00502", "10.1214/26-EJS2506", "10.1093/jrsssb/qkaf008", "10.1073/pnas.2204569119",
 "10.1007/s10994-014-5453-0", "10.1007/s10472-013-9368-4", "10.48550/arXiv.2511.11697", "10.48550/arXiv.2608.07589",
 "10.48550/arXiv.1904.06019", "10.48550/arXiv.1905.03222", "10.1038/s41524-025-01808-x",
 "10.1186/s13321-021-00511-5", "10.1038/s41598-022-09309-3",
]


def get(doi):
    u = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    err = None
    for k in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "citation-audit/0.1"}), timeout=60))["message"]
        except Exception as e:
            err = str(e)
            if "404" in err:
                break
            time.sleep(2 ** (k + 1))
    return {"error": err}


def main(out):
    rows = []
    for d in DOIS:
        m = get(d)
        if "error" in m:
            rows.append({"doi": d, "status": "NOT FOUND: " + m["error"]}); continue
        au = m.get("author", [])
        names = "; ".join(f"{a.get('family', '')}, {a.get('given', '')}".strip(", ") if a.get("family") else a.get("name", "") for a in au)
        yr = (m.get("published-print") or m.get("published-online") or m.get("issued") or {}).get("date-parts", [[None]])[0][0]
        rows.append({"doi": d, "status": "verified", "authors": names, "n_authors": len(au), "year": yr,
                     "title": (m.get("title") or [""])[0], "venue": (m.get("container-title") or [m.get("publisher", "")])[0],
                     "volume": m.get("volume", ""), "issue": m.get("issue", ""), "page": m.get("page", "") or m.get("article-number", ""),
                     "type": m.get("type", "")})
        time.sleep(1.0)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["doi", "status", "authors", "n_authors", "year", "title", "venue", "volume", "issue", "page", "type"])
        w.writeheader(); w.writerows(rows)
    for r in rows:
        print(r["status"][:9], r["doi"], "|", r.get("year"), "|", (r.get("authors") or "")[:40], "|", (r.get("title") or "")[:70], "|", (r.get("venue") or "")[:35])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "references_verified.csv")
