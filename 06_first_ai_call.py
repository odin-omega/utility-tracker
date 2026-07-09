# =====================================================
# FIRST AI API CALL
# The SDK finds ANTHROPIC_API_KEY in the environment
# automatically - the key never appears in code.
# =====================================================

import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=500,
    messages=[
        {"role": "user", "content": "In two sentences, what does a utility company's debt-to-equity ratio tell an analyst?"}
    ],
)

print(response.content[0].text)

response = client.messages.create(
    model="claude-sonnet-4-6",       # which model
    max_tokens=500,                  # response length ceiling
    temperature=.2,                 # 0=consistent, 1=varied.
                                     # Low for analysis, high for creative.
    system="You are a financial analyst covering US utilities. "
           "Be concise and specific. Never give investment advice.",
    messages=[
        {"role": "user", "content": "Assess a utility with D/E of 3.35, net margin 4.9%, ROE 3.7%."}
    ],
)
print(response.content[0].text)