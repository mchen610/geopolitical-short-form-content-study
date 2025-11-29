"""
Quick test script for Gemini API connection.
"""

import os
from dotenv import load_dotenv
from google import genai  # type: ignore[import-untyped]

import config

# Load environment variables
load_dotenv()

def test_gemini():
    print(f"📦 Using model: {config.GEMINI_MODEL}")
    try:
        client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        print("✅ Client created")
        
        # Simple test prompt
        test_prompt = "Say hello in exactly 5 words."
        print(f"\n📤 Sending test prompt: '{test_prompt}'")
        
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=test_prompt,
        )
        
        print(f"📥 Response: {response.text}")
        print("\n✅ Gemini API is working!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    test_gemini()

