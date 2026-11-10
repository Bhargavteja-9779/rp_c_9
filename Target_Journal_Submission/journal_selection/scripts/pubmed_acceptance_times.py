"""Empirical received->accepted times from PubMed article history (E-utilities, efetch XML).
Covers journals indexed in PubMed (incl. Elsevier/OUP/IEEE titles whose dates are not in Crossref).
Uses PubMed <History> PubStatus="received" and "accepted"."""
import sys, time, csv, statistics, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from datetime import date

JOURNALS = {
    "Bioinformatics (OUP)": "Bioinformatics[ta]",
    "Briefings in Bioinformatics (OUP)": "Brief Bioinform[ta]",
    "JAMIA (OUP)": "J Am Med Inform Assoc[ta]",
    "GigaScience (OUP)": "Gigascience[ta]",
    "Bioinformatics Advances (OUP)": "Bioinform Adv[ta]",
    "Computers in Biology and Medicine (Elsevier)": "Comput Biol Med[ta]",
    "Computer Methods and Programs in Biomedicine (Elsevier)": "Comput Methods Programs Biomed[ta]",
    "Artificial Intelligence in Medicine (Elsevier)": "Artif Intell Med[ta]",
    "Journal of Biomedical Informatics (Elsevier)": "J Biomed Inform[ta]",
    "Neural Networks (Elsevier)": "Neural Netw[ta]",
    "Medical Image Analysis (Elsevier)": "Med Image Anal[ta]",
    "Heliyon (Elsevier)": "Heliyon[ta]",
    "IEEE J Biomed Health Inform (IEEE)": "IEEE J Biomed Health Inform[ta]",
    "IEEE Trans Neural Syst Rehabil Eng (IEEE)": "IEEE Trans Neural Syst Rehabil Eng[ta]",
    "IEEE Trans Med Imaging (IEEE)": "IEEE Trans Med Imaging[ta]",
    "IEEE Trans Neural Netw Learn Syst (IEEE)": "IEEE Trans Neural Netw Learn Syst[ta]",
    "IEEE Trans Biomed Eng (IEEE)": "IEEE Trans Biomed Eng[ta]",
    "J Neural Eng (IOP)": "J Neural Eng[ta]",
    "Physiological Measurement (IOP)": "Physiol Meas[ta]",
    "Comput Struct Biotechnol J (Elsevier)": "Comput Struct Biotechnol J[ta]",
    "Patterns (Cell Press)": "Patterns (N Y)[ta]",
    "Biomed Signal Process Control (Elsevier)": "Biomed Signal Process Control[ta]",
    "Expert Syst Appl (Elsevier)": "Expert Syst Appl[ta]",
    "Knowledge-Based Systems (Elsevier)": "Knowl Based Syst[ta]",
    "Information Sciences (Elsevier)": "Inf Sci (N Y)[ta]",
    "Pattern Recognition (Elsevier)": "Pattern Recognit[ta]",
    "Eng Appl Artif Intell (Elsevier)": "Eng Appl Artif Intell[ta]",
    "Applied Soft Computing (Elsevier)": "Appl Soft Comput[ta]",
    "Results in Engineering (Elsevier)": "Results Eng[ta]",
    "IEEE Trans Cybern (IEEE)": "IEEE Trans Cybern[ta]",
    "Information Fusion (Elsevier)": "Inf Fusion[ta]",
    "Biosensors (MDPI - reference only)": "Biosensors (Basel)[ta]",
}
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
UA = {"User-Agent": "research-journal-survey/0.1"}

def get(url):
    for k in range(4):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read()
        except Exception as e: time.sleep(2 ** k)
    raise RuntimeError(url)

def pdate(el):
    try: return date(int(el.findtext("Year")), int(el.findtext("Month")), int(el.findtext("Day")))
    except Exception: return None

def main(out):
    rows = []
    for name, term in JOURNALS.items():
        q = f'{term} AND ("2025/06/01"[dp] : "2026/11/01"[dp]) AND journal article[pt]'
        es = ET.fromstring(get(BASE + "esearch.fcgi?" + urllib.parse.urlencode({"db": "pubmed", "term": q, "retmax": 600, "sort": "pub_date"})))
        ids = [i.text for i in es.iter("Id")]; total = es.findtext("Count")
        days = []
        for k in range(0, len(ids), 200):
            x = ET.fromstring(get(BASE + "efetch.fcgi?" + urllib.parse.urlencode({"db": "pubmed", "id": ",".join(ids[k:k+200]), "retmode": "xml"})))
            for art in x.iter("PubmedArticle"):
                h = {p.get("PubStatus"): pdate(p) for p in art.iter("PubMedPubDate")}
                r, a = h.get("received"), h.get("accepted")
                if r and a and a >= r: days.append((a - r).days)
            time.sleep(0.4)
        if len(days) >= 10:
            qq = statistics.quantiles(days, n=4)
            rows.append([name, total, len(ids), len(days), statistics.median(days), qq[0], qq[2], round(sum(d <= 72 for d in days)/len(days), 3)])
        else:
            rows.append([name, total, len(ids), len(days), "", "", "", ""])
        print(rows[-1], flush=True); time.sleep(0.4)
    with open(out, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["journal", "pubmed_count", "sampled", "n_with_dates", "median_days_received_to_accepted", "q1", "q3", "frac_le_72d"]); w.writerows(rows)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "pubmed_acceptance_times.csv")
