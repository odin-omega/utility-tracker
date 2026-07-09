import anthropic
import json

client = anthropic.Anthropic()

SYSTEM = """You are a financial analyst covering US utilities.
Respond ONLY with valid JSON, no other text, matching exactly:
{"summary": "<2 sentence assessment>",
 "strengths": ["<item>", "<item>"],
 "weaknesses": ["<item>", "<item>"]}"""

# Few-shot: one worked example teaches format + tone
EXAMPLE_USER = "Company: Example Utility. D/E: 1.2, net margin: 14%, ROE: 12%, rank 2 of 15, rating Strong."
EXAMPLE_REPLY = json.dumps({
    "summary": "Example Utility combines low leverage with sector-leading profitability. Its balance sheet strength supports its #2 ranking.",
    "strengths": ["Low debt-to-equity of 1.2", "Net margin of 14% leads peers"],
    "weaknesses": ["Limited upside if rates rise", "Premium valuation risk"],
})

def analyze(description):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        temperature=0.2,
        system=SYSTEM,
        messages=[
            {"role": "user", "content": EXAMPLE_USER},
            {"role": "assistant", "content": EXAMPLE_REPLY},   # the "shot"
            {"role": "user", "content": description},
        ],
    )
    text = response.content[0].text
    return json.loads(text)          # JSON string -> Python dict

result = analyze("Company: PG&E. D/E: 3.35, net margin: 4.9%, ROE: 3.7%, rank 12 of 15, rating Fair.")
print(result["summary"])
print(result["strengths"])
print(result["weaknesses"])