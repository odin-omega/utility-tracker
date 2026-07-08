# =====================================================
# STEP 2: ALL COMPANIES
# Loop the pipeline over ~15 utilities, cache results
# to disk, compute ratios, rank and rate.
# =====================================================

import requests
import json
import time

HEADERS = {"User-Agent": "Evan - learning project - your.email@example.com"}

# The dropdown list, in embryo. Tickers of major US utilities:
UTILITIES = [
    "PCG",   # PG&E
    "EIX",   # Edison International (SCE's parent)
    "SRE",   # Sempra (SDG&E's parent)
    "DUK",   # Duke Energy
    "SO",    # Southern Company
    "NEE",   # NextEra
    "D",     # Dominion
    "AEP",   # American Electric Power
    "XEL",   # Xcel
    "ED",    # Consolidated Edison
    "WEC",   # WEC Energy
    "ES",    # Eversource
    "PEG",   # PSEG
    "AEE",   # Ameren
    "CNP",   # CenterPoint
]


def get_cik_map():
    """Ticker -> zero-padded CIK, for every listed company."""
    url = "https://www.sec.gov/files/company_tickers.json"
    r = requests.get(url, headers=HEADERS)
    mapping = {}
    for entry in r.json().values():
        mapping[entry["ticker"]] = str(entry["cik_str"]).zfill(10)
    return mapping


def get_company_facts(cik):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return None
    return r.json()


from datetime import date

def parse_date(s):
    """'2025-12-31' -> a date object we can subtract."""
    parts = s.split("-")
    return date(int(parts[0]), int(parts[1]), int(parts[2]))


def latest_annual_value(data, tag_candidates):
    """Most recent 10-K value across all candidate tags.
    For flow metrics (entries with a 'start'), only accept
    full-year periods (~365 days), not quarters."""
    gaap = data["facts"]["us-gaap"]
    best = None
    for tag in tag_candidates:
        if tag not in gaap:
            continue
        entries = gaap[tag].get("units", {}).get("USD", [])
        for e in entries:
            if e["form"] != "10-K":
                continue
            if "start" in e:                      # flow metric: check span
                days = (parse_date(e["end"]) - parse_date(e["start"])).days
                if days < 350 or days > 380:
                    continue                       # quarter or oddball: skip
            if best is None or e["end"] > best["end"]:
                best = e
    if best is None:
        return None
    return best["val"]

# note: [e for e in entries if ...] is a "list comprehension" -
# a one-line version of the append-loop you know. Same machine,
# tighter syntax. Read it as "keep each e where the if is true."


def extract_financials(ticker, data):
    """One company's facts -> one clean dict. Your list-of-dicts row."""
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

    if liabilities is None and assets is not None and equity is not None:
        liabilities = assets - equity          # your derivation, now standard

    return {
        "ticker": ticker,
        "name": data["entityName"],
        "revenue": revenue,
        "assets": assets,
        "liabilities": liabilities,
        "equity": equity,
        "net_income": net_income,
    }


def build_cache():
    """Hit the SEC once per company, save everything to one file.
    Run this rarely; everything else reads the file."""
    cik_map = get_cik_map()
    companies = []
    for ticker in UTILITIES:
        print(f"fetching {ticker}...")
        data = get_company_facts(cik_map[ticker])
        if data is None:
            print(f"  FAILED - skipping {ticker}")
            continue
        companies.append(extract_financials(ticker, data))
        time.sleep(0.2)        # stay politely under SEC's rate limit
    with open("companies.json", "w") as f:
        json.dump(companies, f, indent=2)
    print(f"cached {len(companies)} companies to companies.json")


def load_cache():
    with open("companies.json") as f:
        return json.load(f)


# ---- run it ----
#build_cache()                  # comment this line out after first success
companies = load_cache()

for c in companies:
    print(f"{c['ticker']:6} {c['name']}")
