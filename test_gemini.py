from google import genai
from google.genai import types
from core.config import GEMINI_API_KEY, MODEL_NAME
from core.tools import get_tools

client = genai.Client(api_key=GEMINI_API_KEY)
tools = get_tools()

history = [
    types.Content(role="user", parts=[types.Part.from_text(text="Add a task to play chess")]),
    types.Content(role="model", parts=[types.Part.from_function_call(name="manage_tasks", args={"action": "add", "task_description": "play chess"})]),
]

user_parts = [
    types.Part.from_function_response(name="manage_tasks", response={"status": "success"}),
    types.Part.from_text(text="Current screen. What is your next thought and tool action?")
]
history.append(types.Content(role="user", parts=user_parts))

try:
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=history,
        config=types.GenerateContentConfig(tools=tools)
    )
    print("SUCCESS")
except Exception as e:
    print("ERROR:", str(e))
