# =====================================================
# STEP 3: THE WEB APP
# Streamlit turns this file into your sketch.
# Run with:  py -m streamlit run app.py
# =====================================================

import json
import streamlit as st
import yfinance as yf


# ---------- DATA ----------

@st.cache_data
def load_companies():
    with open("companies_scored.json") as f:
        return json.load(f)
# @st.cache_data is a "decorator" - it tells Streamlit to run this
# once and remember the result instead of re-reading the file on
# every click. Same cache idea as companies.json, one level up.


@st.cache_data
def get_stock_history(ticker):
    """One year of daily closing prices."""
    stock = yf.Ticker(ticker)
    hist = stock.history(period="1y")
    return hist["Close"]


companies = load_companies()

def build_summary(c):
    """Plain-English summary assembled from the scored data."""
    lines = []
    lines.append(
        f"{c['name'].title()} ranks #{c['rank']} of 15 utilities "
        f"with an overall strength of {c['rating']}."
    )
    if c["revenue"]:
        lines.append(f"Latest annual revenue: ${c['revenue']/1e9:.1f}B.")
    if c["net_margin"] is not None:
        lines.append(f"Net margin of {c['net_margin']:.1%}.")
    if c["debt_to_equity"] is not None:
        lines.append(f"Debt-to-equity stands at {c['debt_to_equity']:.2f}.")
    return " ".join(lines)


def build_insights(c):
    """Rules-based strengths/weaknesses from the ratios."""
    strengths = []
    weaknesses = []

    de = c["debt_to_equity"]
    if de is not None:
        if de < 1.5:
            strengths.append(f"Low leverage (D/E {de:.2f})")
        elif de > 2.5:
            weaknesses.append(f"High debt-to-equity ratio ({de:.2f})")

    nm = c["net_margin"]
    if nm is not None:
        if nm > 0.12:
            strengths.append(f"Strong net margin ({nm:.1%})")
        elif nm < 0.05:
            weaknesses.append(f"Thin net margin ({nm:.1%})")

    roe = c["roe"]
    if roe is not None:
        if roe > 0.10:
            strengths.append(f"Solid return on equity ({roe:.1%})")
        elif roe < 0.05:
            weaknesses.append(f"Weak return on equity ({roe:.1%})")

    if c["net_income"] is not None and c["net_income"] > 0:
        strengths.append("Profitable in latest fiscal year")
    elif c["net_income"] is not None:
        weaknesses.append("Net loss in latest fiscal year")

    if len(strengths) == 0:
        strengths.append("None identified from current metrics")
    if len(weaknesses) == 0:
        weaknesses.append("None identified from current metrics")

    return strengths, weaknesses

# ---------- PAGE ----------

st.title("UtilityTracker.ai")

# The dropdown from your sketch. Streamlit rule: every st.something()
# paints an element on the page, top to bottom, in code order.
names = [f"{c['ticker']} - {c['name']}" for c in companies]
choice = st.selectbox("Select company", names)

ticker = choice.split(" - ")[0]

# Find the selected company's dict - your find_client() pattern, live
company = None
for c in companies:
    if c["ticker"] == ticker:
        company = c
        break

st.header(company["name"])

# ---------- METRICS ROW (rank / rating from the sketch) ----------
col1, col2, col3 = st.columns(3)
col1.metric("Company Rank", f"#{company['rank']} of {len(companies)}")
col2.metric("Overall Strength", company["rating"])
col3.metric("Score", f"{company['score']:.0f}/100" if company["score"] else "-")

# ---------- FINANCIALS ----------
st.subheader("Key Financials")
col1, col2 = st.columns(2)

with col1:
    if company["revenue"]:
        st.write(f"**Revenue:** ${company['revenue']:,.0f}")
    if company["net_income"]:
        st.write(f"**Net income:** ${company['net_income']:,.0f}")
    if company["assets"]:
        st.write(f"**Assets:** ${company['assets']:,.0f}")

with col2:
    if company["debt_to_equity"] is not None:
        st.write(f"**Debt-to-equity:** {company['debt_to_equity']:.2f}")
    if company["net_margin"] is not None:
        st.write(f"**Net margin:** {company['net_margin']:.1%}")
    if company["roe"] is not None:
        st.write(f"**ROE:** {company['roe']:.1%}")

# ---------- STOCK CHART ----------
st.subheader("Stock Price - 1 Year")
prices = get_stock_history(ticker)
if len(prices) > 0:
    st.line_chart(prices)
    st.write(f"Latest close: ${prices.iloc[-1]:.2f}")
else:
    st.write("No price data available")

# ---------- SUMMARY ----------
st.subheader("Summary")
st.write(build_summary(company))

st.subheader("Insights")
strengths, weaknesses = st.columns(2)[0], None   # delete this line if pasting fresh
col1, col2 = st.columns(2)
s_list, w_list = build_insights(company)
with col1:
    st.markdown("**Strengths**")
    for s in s_list:
        st.write(f"• {s}")
with col2:
    st.markdown("**Weaknesses**")
    for w in w_list:
        st.write(f"• {w}")