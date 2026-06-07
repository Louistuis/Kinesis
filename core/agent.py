import json
import io
from google import genai
from google.genai import types

from core.mac_os_bridge import MacBridge
from core.config import GEMINI_API_KEY, MODEL_NAME, WAIT_TIME_SECONDS
from core.tools import get_tools
from core.prompts import SYSTEM_INSTRUCTION
from core.executor import ActionExecutor

class MacAgent:
    def __init__(self, bridge=None):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.bridge = bridge if bridge else MacBridge()
        self.executor = ActionExecutor(self.bridge)
        self.history = []
        
        self.tools = get_tools()
        self.system_instruction = SYSTEM_INSTRUCTION

    def _prepare_vision_payload(self, previous_responses):
        """Captures screen and packages it with previous responses for Gemini."""
        screenshot, logical_width, logical_height = self.bridge.capture_screen()
        
        img_byte_arr = io.BytesIO()
        if screenshot.mode in ('RGBA', 'P'):
            screenshot = screenshot.convert('RGB')
            
        try:
            screenshot.save("debug_screenshot.jpg", format='JPEG', quality=85)
        except Exception:
            pass
            
        screenshot.save(img_byte_arr, format='JPEG', quality=85)
        img_bytes = img_byte_arr.getvalue()
        
        parts = []
        if previous_responses:
            parts.extend(previous_responses)
            
        parts.extend([
            types.Part.from_bytes(data=img_bytes, mime_type='image/jpeg'),
            types.Part.from_text(text="Current screen. What is your next thought and tool action?")
        ])
        return parts, logical_width, logical_height

    def _query_model(self):
        """Queries the Gemini model and returns the response."""
        return self.client.models.generate_content(
            model=MODEL_NAME,
            contents=self.history,
            config=types.GenerateContentConfig(
                system_instruction=self.system_instruction,
                tools=self.tools,
                temperature=0.0
            )
        )

    def run(self, task: str):
        self.history = [
            types.Content(role="user", parts=[
                types.Part.from_text(text=f"Please accomplish the following task: {task}")
            ])
        ]
        
        previous_function_responses = []
        
        while True:
            # 1. Capture & Prepare
            yield {"type": "status", "message": "Capturing screen..."}
            parts, logical_width, logical_height = self._prepare_vision_payload(previous_function_responses)
            previous_function_responses = []
            
            # To drastically reduce latency, we strip previous screenshots from the history.
            # We only need the latest screenshot to know what to do next. The text history preserves context.
            for content in self.history:
                if content is None:
                    continue
                if content.role == "user" and hasattr(content, "parts"):
                    # Keep only non-image parts
                    new_parts = []
                    for p in content.parts:
                        if not hasattr(p, "inline_data") or not p.inline_data:
                            if not hasattr(p, "image") or not p.image:
                                new_parts.append(p)
                    content.parts = new_parts
            
            self.history.append(types.Content(role="user", parts=parts))
            
            # 2. Query Model
            yield {"type": "info", "message": "📸 Capturing screen and querying Gemini Vision API (this usually takes 5-10 seconds)..."}
            yield {"type": "status", "message": "Reasoning... querying Gemini..."}
            
            try:
                import json
                with open('cursor_pos.txt', 'w') as f:
                    # We don't have x,y here, just state
                    f.write(json.dumps({"state": "idle"}))
            except: pass
            
            try:
                response = self._query_model()
            except Exception as e:
                yield {"type": "error", "message": f"Error communicating with model: {e}"}
                break

            if response.candidates and hasattr(response.candidates[0], 'content') and response.candidates[0].content:
                self.history.append(response.candidates[0].content)

            # 3. Handle Empty Responses
            function_calls = response.function_calls
            if not function_calls and not response.text:
                finish_reason = response.candidates[0].finish_reason if response.candidates else "UNKNOWN"
                yield {"type": "info", "message": f"Empty response. Reason: {finish_reason}. Forcing retry..."}
                self.history.append(types.Content(role="user", parts=[types.Part.from_text(text="You returned an empty response. Please execute a tool call or output your reasoning.")]))
                continue
                
            if not function_calls:
                yield {"type": "info", "message": response.text}
                break
                
            # 4. Execute Tools
            task_finished = False
            action_executed_this_turn = False
            
            for fc in function_calls:
                name = fc.name
                args = fc.args
                
                # Block chained actions
                if action_executed_this_turn and name != "task_complete":
                    result_dict = {"error": "FATAL: Multiple actions chained. Wait for screenshot!", "url": "http://localhost"}
                    yield {"type": "info", "message": f"Blocked chained action: {name}"}
                    previous_function_responses.append(types.Part.from_function_response(name=name, response=result_dict))
                    continue
                
                gen = self.executor.execute_tool(name, args, logical_width, logical_height, response.text)
                while True:
                    try:
                        yielded_val = next(gen)
                        yield yielded_val
                    except StopIteration as e:
                        event, result_dict, is_finished, is_executed = e.value
                        break
                        
                if is_executed:
                    action_executed_this_turn = True
                if is_finished:
                    task_finished = True
                    
                previous_function_responses.append(
                    types.Part.from_function_response(name=name, response=result_dict)
                )
                
                if action_executed_this_turn and "error" not in result_dict and not task_finished:
                    self.bridge.wait(0.5)

            if task_finished:
                break
                
            self.bridge.wait(WAIT_TIME_SECONDS)
