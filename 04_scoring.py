# =====================================================
# STEP 2B: RATIOS, SCORING, RANK, RATING
# Raw financials -> ratios -> 0-100 score -> rank + label
# Deterministic and defensible: every number traceable.
# =====================================================

import json


def load_cache():
    with open("companies.json") as f:
        return json.load(f)


def compute_ratios(c):
    """Add ratio fields to one company dict. None-safe:
    a missing input just means that ratio is None."""
    c["debt_to_equity"] = None
    c["net_margin"] = None
    c["roe"] = None
    c["roa"] = None

    if c["liabilities"] is not None and c["equity"] not in (None, 0):
        c["debt_to_equity"] = c["liabilities"] / c["equity"]
    if c["net_income"] is not None and c["revenue"] not in (None, 0):
        c["net_margin"] = c["net_income"] / c["revenue"]
    if c["net_income"] is not None and c["equity"] not in (None, 0):
        c["roe"] = c["net_income"] / c["equity"]
    if c["net_income"] is not None and c["assets"] not in (None, 0):
        c["roa"] = c["net_income"] / c["assets"]
    return c


def score_metric(value, worst, best):
    """Scale a value to 0-100 between a worst and best bound.
    Works whether higher-is-better (worst < best) or
    lower-is-better (worst > best, like debt-to-equity)."""
    if value is None:
        return None
    position = (value - worst) / (best - worst)
    position = max(0.0, min(1.0, position))     # clamp into range
    return position * 100


def score_company(c):
    """Weighted blend of metric scores -> one 0-100 number.
    Weights are an FP&A judgment call - argue with them!"""
    scores = {
        "debt_to_equity": score_metric(c["debt_to_equity"], worst=4.0, best=1.0),
        "net_margin":     score_metric(c["net_margin"],     worst=0.0, best=0.20),
        "roe":            score_metric(c["roe"],            worst=0.0, best=0.15),
        "roa":            score_metric(c["roa"],            worst=0.0, best=0.05),
    }
    weights = {
        "debt_to_equity": 0.40,   # leverage = the utility risk story
        "net_margin":     0.25,
        "roe":            0.20,
        "roa":            0.15,
    }

    total = 0.0
    weight_used = 0.0
    for metric, s in scores.items():
        if s is None:
            continue                  # missing metric: redistribute
        total += s * weights[metric]
        weight_used += weights[metric]

    if weight_used == 0:
        return None                   # nothing scoreable at all
    return total / weight_used        # renormalize over what existed


def strength_label(score):
    """0-100 -> the five-bucket rating from your sketch."""
    if score is None:
        return "Insufficient data"
    if score >= 80:
        return "Very Strong"
    elif score >= 60:
        return "Strong"
    elif score >= 40:
        return "Fair"
    elif score >= 20:
        return "Weak"
    else:
        return "Very Weak"


# ---- run it ----
companies = load_cache()

for c in companies:
    compute_ratios(c)
    c["score"] = score_company(c)
    c["rating"] = strength_label(c["score"])

# Rank: sort by score, best first. Companies with no score sink.
companies.sort(key=lambda c: c["score"] or 0, reverse=True)
for i, c in enumerate(companies):
    c["rank"] = i + 1
# enumerate() = loop with a counter: i is 0,1,2... alongside each item

print(f"{'RANK':5} {'TICKER':7} {'SCORE':6} {'RATING':12} {'D/E':6} {'MARGIN':7}")
for c in companies:
    de = f"{c['debt_to_equity']:.2f}" if c['debt_to_equity'] is not None else "-"
    nm = f"{c['net_margin']:.1%}" if c['net_margin'] is not None else "-"
    score = f"{c['score']:.0f}" if c['score'] is not None else "-"
    print(f"{c['rank']:<5} {c['ticker']:7} {score:6} {c['rating']:12} {de:6} {nm:7}")

# Save the scored version - this file is what Streamlit will read
with open("companies_scored.json", "w") as f:
    json.dump(companies, f, indent=2)
print("\nwrote companies_scored.json")