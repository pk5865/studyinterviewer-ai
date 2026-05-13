# Create test_gemini.py in backend/
import os
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
try:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Say hello in one sentence."
    )
    print("✅ Gemini works:", response.text)
except Exception as e:
    print("❌ Error:", e)