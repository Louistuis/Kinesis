from google import genai
from google.genai import types
from core.config import GEMINI_API_KEY, MODEL_NAME
from core.tools import get_tools
from core.prompts import SYSTEM_INSTRUCTION
from PIL import Image
import io

img = Image.new('RGB', (100, 100), color = 'red')
img_byte_arr = io.BytesIO()
img.save(img_byte_arr, format='JPEG')
img_bytes = img_byte_arr.getvalue()

client = genai.Client(api_key=GEMINI_API_KEY)
tools = get_tools()

history = [
    types.Content(role="user", parts=[types.Part.from_text(text="Please accomplish the following task: play chess with the bot.")]),
    types.Content(role="user", parts=[types.Part.from_text(text="Current screen. What is your next thought and tool action?")]),
    types.Content(role="model", parts=[types.Part.from_function_call(name="manage_tasks", args={"action": "add", "task_description": "play chess"})]),
    types.Content(role="user", parts=[
        types.Part.from_function_response(name="manage_tasks", response={"status": "success", "url": "http://localhost"}),
        types.Part.from_bytes(data=img_bytes, mime_type='image/jpeg'),
        types.Part.from_text(text="Current screen. What is your next thought and tool action?")
    ])
]

try:
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=history,
        config=types.GenerateContentConfig(
            tools=tools,
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.0
        )
    )
    print("SUCCESS")
except Exception as e:
    print("ERROR:", str(e))
