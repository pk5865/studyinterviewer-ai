import os
from dotenv import load_dotenv
load_dotenv()  # Load .env file

# Get API key from environment (NOT hardcoded)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("❌ GROQ_API_KEY not found in .env file")
    exit(1)

from groq import Groq
client = Groq(api_key=GROQ_API_KEY)

print("Testing Groq directly...")
try:
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": "Say hello in one sentence."}],
        temperature=0.4,
        max_tokens=100
    )
    print("✅ Groq works! Response:", response.choices[0].message.content)
except Exception as e:
    print("❌ Groq FAILED:", str(e))