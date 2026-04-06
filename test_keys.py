import os
import google.generativeai as genai
from dotenv import load_dotenv
import traceback

load_dotenv()

api_keys_str = os.getenv("GEMINI_API_KEYS") or os.getenv("GEMINI_API_KEY", "")
api_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]

print(f"Total keys found: {len(api_keys)}")

for idx, key in enumerate(api_keys):
    masked = key[:6] + "..." + key[-4:] if len(key) > 10 else "invalid"
    print(f"\n--- Testing Key {idx+1} ({masked}) ---")
    genai.configure(api_key=key)
    try:
        models = genai.list_models()
        count = 0
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                count += 1
        print(f"✅ Success! Found {count} text models.")
    except Exception as e:
        print(f"❌ Failed: {type(e).__name__} - {e}")
