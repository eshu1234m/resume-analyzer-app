import google.generativeai as genai
from dotenv import load_dotenv
import os

# Explicitly load the .env file from the current directory
load_dotenv(dotenv_path=".env")

print("--- Starting Model Availability Check ---")

try:
    # 1. Configure the API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Could not find GEMINI_API_KEY in your .env file.")
    
    genai.configure(api_key=api_key)
    print("✅ API Key configured successfully.")

    # 2. List all available models that support 'generateContent'
    print("\n🔍 Searching for models you can use...")
    
    found_models = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"  -> Found available model: {m.name}")
            found_models = True
            
    if not found_models:
        print("\n❌ No models supporting 'generateContent' were found for your API key.")
        print("This could be a permissions issue or a regional restriction in your Google Cloud project.")

except Exception as e:
    print(f"\n🚨 An error occurred during the check: {e}")

print("\n--- Check Complete ---")

