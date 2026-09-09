import os
from groq import Groq
from dotenv import load_dotenv
from dashboard.services import get_dashboard_data

load_dotenv()

# Configure Gemini
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL_NAME = "llama-3.1-8b-instant"
def build_system_prompt():
    data = get_dashboard_data()

    hourly_text = ", ".join(
        f"{h['hour']}:00 → {h['value']} kWh"
        for h in data["hourly_profile"]
    )

    daily_text = ", ".join(
        f"{d['day']}: {d['value']} kWh"
        for d in data["daily_consumption"]
    )


    return f"""
You are the official assistant for the Energy Consumption Prediction Website.

STRICT RULES:
1. You must ONLY answer questions related to:
   - This website
   - Its features and pages
   - Energy prediction shown on this website
   - Input fields (temperature, humidity, HVAC, Square Footage, Occupancy, Holiday)
   - Dashboard, analytics, and prediction results
   - How the model works at a high level (no math, no code)
   - *Give some general feedback on how to be sustainable and reduce energy usage only if asked*

2. You must NOT:
   - Give general energy-saving advice unrelated to this website
   - Answer personal, medical, financial, or unrelated questions
   - Answer questions not connected to the website

3. If a question is OUT OF SCOPE:
   - Politely say you can only help with this website
   - Guide the user to relevant features if possible

WEBSITE CONTEXT:
- Backend: Flask + XGBoost model
- Frontend: React + Tailwind
- Predict page takes user inputs and returns predicted energy (kWh)
- Lag features are automatically generated from past predictions
- Dashboard shows energy trends and analytics
- Chatbot helps users understand and navigate the site
- Average Energy Consumption: {data['kpis']['avg_consumption']} kWh/day
- Peak Energy Usage: {data['kpis']['peak_usage']} kWh
- Minimum Energy Usage: {data['kpis']['min_usage']} kWh
- Renewable Energy Share: {data['kpis']['renewable_share']}%
- Hourly Energy Profile: {hourly_text}
- Daily Consumption: {daily_text}

Tone:
- Clear
- Helpful
- Short and precise
"""


def chat_with_bot(messages):
    system_prompt = build_system_prompt()
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            *messages
        ],
        temperature=0.3,
        max_tokens=300
    )

    return completion.choices[0].message.content


