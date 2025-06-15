import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get your Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("--- Available Gemini Models ---")
        for m in genai.list_models():
            # Filter for text generation models that support generateContent
            if 'generateContent' in m.supported_generation_methods:
                print(f"Model Name: {m.name}")
                print(f"  Description: {m.description}")
                print(f"  Supported Methods: {m.supported_generation_methods}")
                print("-" * 30)
    except Exception as e:
        print(f"ERROR: Could not configure Gemini API or list models: {e}")
        print("Please ensure your GEMINI_API_KEY is correct and valid.")
else:
    print("ERROR: GEMINI_API_KEY not found in .env. Please set it.")