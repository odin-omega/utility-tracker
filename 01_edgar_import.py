import requests

# The SEC requires you to identify yourself in every request.
# No key needed - just a User-Agent header with contact info.
# Requests WITHOUT this get blocked with a 403.
HEADERS = {"User-Agent": "Evan - learning project - evansatre@gmail.com"}

# Official SEC mapping of every ticker to its CIK number
url = "https://www.sec.gov/files/company_tickers.json"
r = requests.get(url, headers=HEADERS)
print(r.status_code)          # want 200

tickers = r.json()

# It's a dict of dicts: {"0": {"cik_str": ..., "ticker": ..., "title": ...}, ...}
# Loop it to find PG&E Corp (ticker: PCG)
for entry in tickers.values():
    if entry["ticker"] == "PCG":
        print(entry)
        cik = str(entry["cik_str"]).zfill(10)   # pad to 10 digits with zeros
        print(cik)

        # companyfacts = every number the company ever reported, as JSON
facts_url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
r = requests.get(facts_url, headers=HEADERS)
print(r.status_code)

data = r.json()
print(data["entityName"])

# This JSON is HUGE. Don't print it. Save it and browse it instead:
import json
with open("pge_facts.json", "w") as f:
    json.dump(data, f, indent=2)
print("saved - open pge_facts.json in the sidebar")