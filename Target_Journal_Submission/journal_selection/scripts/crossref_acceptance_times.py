"""Compute empirical submission-to-acceptance times from Crossref-deposited article
history assertions ("received", "accepted"). Only articles that carry BOTH dates are used.
Output: CSV with per-journal n, median, IQR, fraction <=72 days.
This is an independent check; it measures received->accepted for PUBLISHED papers only
(rejected papers are invisible), and only for publishers that deposit these assertions."""
import json, sys, time, statistics, urllib.request, urllib.parse, csv
from datetime import datetime

JOURNALS = {
    # name: ISSN
    "Journal of Big Data (Springer)": "2196-1115",
    "Complex & Intelligent Systems (Springer)": "2198-6053",
    "Journal of Cheminformatics (Springer/BMC)": "1758-2946",
    "Artificial Intelligence Review (Springer)": "1573-7462",
    "Scientific Reports (Nature)": "2045-2322",
    "J. King Saud Univ. CIS (Springer, 2025-)": "1319-1578",
    "Neural Computing and Applications (Springer)": "1433-3058",
    "Journal of Cloud Computing (Springer)": "2192-113X",
    "npj Digital Medicine (Nature)": "2398-6352",
    "Scientific Data (Nature)": "2052-4463",
    "BMC Bioinformatics": "1471-2105",
    "BMC Medical Informatics and Decision Making": "1472-6947",
    "Cognitive Computation (Springer)": "1866-9964",
    "Journal of Intelligent Manufacturing (Springer)": "1572-8145",
    "Data Mining and Knowledge Discovery (Springer)": "1573-756X",
    "Machine Learning (Springer)": "1573-0565",
    "Applied Intelligence (Springer)": "1573-7497",
    "International Journal of Machine Learning and Cybernetics": "1868-808X",
    "Communications Engineering (Nature)": "2731-3395",
    "Journal of Cheminformatics": "1758-2946",
}

def parse(d):
    for fmt in ("%d %B %Y", "%Y-%m-%d"):
        try: return datetime.strptime(d.strip(), fmt)
        except Exception: pass
    return None

def fetch(issn, rows=1000, since="2025-05-01"):
    out, cursor = [], "*"
    while len(out) < rows:
        q = urllib.parse.urlencode({"filter": f"from-pub-date:{since},type:journal-article",
             "rows": 500, "cursor": cursor, "select": "DOI,assertion,published"})
        url = f"https://api.crossref.org/journals/{issn}/works?{q}"
        req = urllib.request.Request(url, headers={"User-Agent": "research-journal-survey/0.1"})
        try:
            d = json.load(urllib.request.urlopen(req, timeout=60))["message"]
        except Exception as e:
            print("ERR", issn, e, file=sys.stderr); break
        items = d["items"]
        if not items: break
        out += items; cursor = d.get("next-cursor")
        time.sleep(0.5)
    return out

def main(outcsv):
    rows = []
    for name, issn in JOURNALS.items():
        items = fetch(issn)
        days = []
        for it in items:
            a = {x.get("name"): x.get("value") for x in it.get("assertion", []) if x.get("value")}
            r, ac = a.get("received"), a.get("accepted")
            if r and ac:
                r, ac = parse(r), parse(ac)
                if r and ac and ac >= r: days.append((ac - r).days)
        if days:
            q = statistics.quantiles(days, n=4)
            rows.append([name, issn, len(items), len(days), statistics.median(days), q[0], q[2],
                         round(sum(d <= 72 for d in days) / len(days), 3)])
        else:
            rows.append([name, issn, len(items), 0, "", "", "", ""])
        print(rows[-1], flush=True)
    with open(outcsv, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["journal", "issn", "n_records", "n_with_dates", "median_days_received_to_accepted", "q1", "q3", "frac_le_72d"]); w.writerows(rows)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "crossref_acceptance_times.csv")
