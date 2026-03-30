import google.generativeai as genai
import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from config.settings import get_current_api_key

load_dotenv()
genai.configure(api_key=get_current_api_key())

try:
    print("Available Gemini models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
