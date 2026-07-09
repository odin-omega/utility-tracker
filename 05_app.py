# =====================================================
# STEP 3: THE WEB APP
# Streamlit turns this file into your sketch.
# Run with:  py -m streamlit run app.py
# =====================================================

import json
import streamlit as st
import yfinance as yf
import anthropic

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

@st.cache_data
def get_ai_analysis(ticker, description):
    """One API call returns summary + strengths + weaknesses.
    Cached: each company is analyzed once per session, then free."""
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

    system = """You are a financial analyst covering US utilities.
Respond ONLY with valid JSON, no other text, matching exactly:
{"summary": "<2-3 sentence assessment>",
 "strengths": ["<item>", "<item>", "<item>"],
 "weaknesses": ["<item>", "<item>", "<item>"]}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=700,
            temperature=0.2,
            system=system,
            messages=[{"role": "user", "content": description}],
        )
        text = response.content[0].text
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        return {
            "summary": f"AI analysis unavailable ({e})",
            "strengths": ["-"],
            "weaknesses": ["-"],
        }


def describe_company(c):
    """Turn the scored dict into the prompt's input text."""
    parts = [f"Company: {c['name']} ({c['ticker']})."]
    parts.append(f"Rank {c['rank']} of 15, rating {c['rating']}.")
    if c["debt_to_equity"] is not None:
        parts.append(f"Debt-to-equity: {c['debt_to_equity']:.2f}.")
    if c["net_margin"] is not None:
        parts.append(f"Net margin: {c['net_margin']:.1%}.")
    if c["roe"] is not None:
        parts.append(f"ROE: {c['roe']:.1%}.")
    if c["revenue"]:
        parts.append(f"Annual revenue: ${c['revenue']/1e9:.1f}B.")
    return " ".join(parts)

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
analysis = get_ai_analysis(company["ticker"], describe_company(company))
st.write(analysis["summary"])

st.subheader("Insights")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Strengths**")
    for s in analysis["strengths"]:
        st.write(f"• {s}")
with col2:
    st.markdown("**Weaknesses**")
    for w in analysis["weaknesses"]:
        st.write(f"• {w}")