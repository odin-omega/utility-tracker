import requests
import json

HEADERS = {"User-Agent": "Evan - learning project - your.email@example.com"}


def get_company_facts(cik):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return None
    return r.json()


def latest_annual_value(data, tag_candidates):
    """Find the most recent 10-K (annual) value for the first
    tag that exists. Returns None if nothing matches."""
    gaap = data["facts"]["us-gaap"]
    for tag in tag_candidates:
        if tag not in gaap:
            continue                     # try the next candidate
        entries = gaap[tag]["units"]["USD"]
        annual = []
        for e in entries:
            if e["form"] == "10-K":      # annual filings only
                annual.append(e)
        if len(annual) == 0:
            continue
        # most recent = biggest period-end date; ISO dates sort as strings
        annual.sort(key=lambda e: e["end"])
        return annual[-1]["val"]
    return None


# ---- run it ----
cik = "0001004980"    # PG&E, from checkpoint 1

data = get_company_facts(cik)
print(data["entityName"])

revenue = latest_annual_value(data, [
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
])
assets = latest_annual_value(data, ["Assets"])
liabilities = latest_annual_value(data, ["Liabilities"])
equity = latest_annual_value(data, [
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
])
net_income = latest_annual_value(data, ["NetIncomeLoss"])

def show(label, value):
    if value is None:
        print(f"{label:14} MISSING")
    else:
        print(f"{label:14} {value:,}")

liabilities = latest_annual_value(data, ["Liabilities"])

# PG&E doesn't report a total-liabilities tag - derive from
# the accounting identity: A = L + E, so L = A - E

liabilities_derived = False
if liabilities is None and assets is not None and equity is not None:
    liabilities = assets - equity
    liabilities_derived = True
   
  
show("Revenue:", revenue)
show("Assets:", assets)
show("Liabilities:", liabilities)
if liabilities_derived:
    print("               (derived from A - E)")
show("Equity:", equity)
show("Net income:", net_income)