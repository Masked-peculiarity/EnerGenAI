import json
from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROMPT = """
Extract energy-related values from the text and return ONLY JSON.

Fields:
Temperature
Humidity
Occupancy
SquareFootage
RenewableEnergy
HVAC (1=on, 0=off)
Lighting (1=on, 0=off)
Holiday (1=yes, 0=no)

Rules:
- Infer intelligently
- Missing values → 0
- No explanation, only JSON

Text:
\"\"\"
{TEXT}
\"\"\"
"""

def extract_features(text: str) -> dict:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": PROMPT.replace("{TEXT}", text)}],
        temperature=0
    )

    return json.loads(response.choices[0].message.content)
