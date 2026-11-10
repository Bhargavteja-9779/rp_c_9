"""Empirical received->accepted times from PMC full-text JATS <history> dates via the Europe PMC REST API.
Useful for open-access journals (e.g. IEEE TNSRE, Heliyon) whose dates are absent from PubMed/Crossref."""
import sys, time, csv, statistics, urllib.request, urllib.parse, json, re
import xml.etree.ElementTree as ET
from datetime import date
UA = {"User-Agent": "research-journal-survey/0.1"}
B = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
def get(u):
    for k in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90).read()
        except Exception: time.sleep(2 ** k)
    return None
def d(el):
    try: return date(int(el.findtext("year")), int(el.findtext("month")), int(el.findtext("day")))
    except Exception: return None
def journal(query, n=250):
    ids, cur = [], "*"
    while len(ids) < n:
        u = B + "search?" + urllib.parse.urlencode({"query": query + " AND OPEN_ACCESS:y AND IN_PMC:y", "format": "json", "pageSize": 200, "cursorMark": cur, "resultType": "lite"})
        j = json.loads(get(u)); r = j["resultList"]["result"]
        if not r: break
        ids += [x["pmcid"] for x in r if x.get("pmcid")]; cur = j.get("nextCursorMark")
        if not cur or len(r) < 200: break
    days = []
    for p in ids[:n]:
        x = get(B + f"{p}/fullTextXML")
        if not x: continue
        try: t = ET.fromstring(x)
        except Exception: continue
        h = {e.get("date-type"): d(e) for e in t.iter("date") if e.get("date-type") in ("received", "accepted", "rev-recd")}
        if h.get("received") and h.get("accepted") and h["accepted"] >= h["received"]:
            days.append((h["accepted"] - h["received"]).days)
        time.sleep(0.15)
    return len(ids), days
if __name__ == "__main__":
    J = {
      "IEEE TNSRE": 'JOURNAL:"IEEE Trans Neural Syst Rehabil Eng" AND (FIRST_PDATE:[2025-03-01 TO 2026-11-01])',
      "IEEE Open J Eng Med Biol": 'JOURNAL:"IEEE Open J Eng Med Biol" AND (FIRST_PDATE:[2025-01-01 TO 2026-11-01])',
      "IEEE J Transl Eng Health Med": 'JOURNAL:"IEEE J Transl Eng Health Med" AND (FIRST_PDATE:[2025-01-01 TO 2026-11-01])',
    }
    rows = []
    for k, q in J.items():
        n, days = journal(q)
        if days:
            qq = statistics.quantiles(days, n=4)
            rows.append([k, n, len(days), statistics.median(days), qq[0], qq[2], round(sum(v <= 72 for v in days)/len(days), 3), round(sum(v <= 60 for v in days)/len(days), 3)])
        else: rows.append([k, n, 0, "", "", "", "", ""])
        print(rows[-1], flush=True)
    with open(sys.argv[1] if len(sys.argv) > 1 else "europepmc_acceptance_times.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["journal", "n_pmc", "n_with_dates", "median", "q1", "q3", "frac_le_72", "frac_le_60"]); w.writerows(rows)
