import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google import genai
from google.genai import types
from core.config import GEMINI_API_KEY

def test_model(model_name):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        tools = [
            types.Tool(
                computer_use=types.ComputerUse(
                    environment=types.Environment.ENVIRONMENT_DESKTOP
                )
            )
        ]
        
        response = client.models.generate_content(
            model=model_name,
            contents="Click on the center of the screen.",
            config=types.GenerateContentConfig(
                tools=tools,
                temperature=0.0
            )
        )
        print(f"[SUCCESS] {model_name} supports ComputerUse tool!")
        if response.function_calls:
            print(f"Function calls: {[f.name for f in response.function_calls]}")
    except Exception as e:
        print(f"[ERROR] {model_name} failed: {e}")

if __name__ == "__main__":
    test_model("gemini-3.5-flash-preview")
    test_model("gemini-3.0-pro")
    test_model("gemini-3.1-flash-lite-preview")
