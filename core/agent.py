import json
import io
import traceback
from google import genai
from google.genai import types

from core.mac_os_bridge import MacBridge
from core.config import GEMINI_API_KEY, MODEL_NAME, REASONING_MODEL_NAME, WAIT_TIME_SECONDS
from core.tools import get_brain_tools, get_hands_tools
from core.prompts import BRAIN_SYSTEM_INSTRUCTION, HANDS_SYSTEM_INSTRUCTION
from core.executor import ActionExecutor

class MacAgent:
    def __init__(self, bridge=None):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.bridge = bridge if bridge else MacBridge()
        self.executor = ActionExecutor(self.bridge)
        self.history = []
        
        self.brain_tools = get_brain_tools()
        self.hands_tools = get_hands_tools()

    def _prepare_vision_payload(self, previous_responses, prompt_text="Current screen. What is your next thought and tool action?"):
        screenshot, logical_width, logical_height = self.bridge.capture_screen()
        
        img_byte_arr = io.BytesIO()
        if screenshot.mode in ('RGBA', 'P'):
            screenshot = screenshot.convert('RGB')
            
        screenshot.save(img_byte_arr, format='JPEG', quality=85)
        img_bytes = img_byte_arr.getvalue()
        
        parts = []
        if previous_responses:
            parts.extend(previous_responses)
            
        parts.extend([
            types.Part.from_bytes(data=img_bytes, mime_type='image/jpeg'),
            types.Part.from_text(text=prompt_text)
        ])
        return parts, logical_width, logical_height

    def _query_brain(self):
        return self.client.models.generate_content(
            model=REASONING_MODEL_NAME,
            contents=self.history,
            config=types.GenerateContentConfig(
                system_instruction=BRAIN_SYSTEM_INSTRUCTION,
                tools=self.brain_tools,
                temperature=0.0
            )
        )

    def _query_hands(self, instruction: str, logical_width: int, logical_height: int):
        parts, _, _ = self._prepare_vision_payload([], prompt_text=f"HANDOFF INSTRUCTION: {instruction}")
        
        return self.client.models.generate_content(
            model=MODEL_NAME,
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(
                system_instruction=HANDS_SYSTEM_INSTRUCTION,
                tools=self.hands_tools,
                temperature=0.0
            )
        )

    def run(self, task: str):
        if not self.history:
            self.history = [
                types.Content(role="user", parts=[
                    types.Part.from_text(text=f"Please accomplish the following task: {task}")
                ])
            ]
        elif task:
            self.history.append(
                types.Content(role="user", parts=[
                    types.Part.from_text(text=f"New instruction: {task}")
                ])
            )
            
        previous_function_responses = []
        
        while True:
            # 1. Capture & Prepare for Brain
            yield {"type": "status", "message": "Capturing screen for Brain..."}
            parts, logical_width, logical_height = self._prepare_vision_payload(previous_function_responses)
            previous_function_responses = []
            
            for content in self.history:
                if content is None: continue
                if content.role == "user" and hasattr(content, "parts"):
                    new_parts = [p for p in content.parts if not (hasattr(p, "inline_data") and p.inline_data) and not (hasattr(p, "image") and p.image)]
                    content.parts = new_parts
            
            self.history.append(types.Content(role="user", parts=parts))
            
            yield {"type": "info", "message": f"🧠 Querying Brain ({REASONING_MODEL_NAME})..."}
            
            try:
                with open('cursor_pos.txt', 'w') as f: f.write(json.dumps({"state": "idle"}))
            except: pass
            
            try:
                brain_response = self._query_brain()
            except Exception as e:
                yield {"type": "error", "message": f"Brain Error: {e}\n{traceback.format_exc()}"}
                break

            if brain_response.candidates and hasattr(brain_response.candidates[0], 'content') and brain_response.candidates[0].content:
                self.history.append(brain_response.candidates[0].content)

            function_calls = brain_response.function_calls
            if not function_calls:
                self.history.append(types.Content(role="user", parts=[types.Part.from_text(text="You MUST use a tool. Use handoff_action or task_complete.")]))
                continue
                
            task_finished = False
            
            for fc in function_calls:
                name = fc.name
                args = fc.args
                brain_thought = brain_response.text
                
                if name == "handoff_action":
                    instruction = args.get("instruction", "")
                    
                    # Log Brain's handoff
                    yield {"type": "action", "action_name": "handoff", "args": {"instruction": instruction}, "thought": brain_thought, "native_coords": None}
                    
                    yield {"type": "info", "message": f"✋ Handoff to Hands ({MODEL_NAME}): '{instruction}'"}
                    
                    try:
                        hands_response = self._query_hands(instruction, logical_width, logical_height)
                        hands_calls = hands_response.function_calls
                        if hands_calls:
                            hc = hands_calls[0]
                            # Execute Hands Tool
                            gen = self.executor.execute_tool(hc.name, hc.args, logical_width, logical_height, "")
                            while True:
                                try:
                                    yielded_val = next(gen)
                                    yield yielded_val
                                except StopIteration as e:
                                    _, result_dict, _, _ = e.value
                                    break
                                    
                            previous_function_responses.append(
                                types.Part.from_function_response(name=name, response={"status": "Hands executed successfully", "hands_tool_called": hc.name})
                            )
                        else:
                            previous_function_responses.append(
                                types.Part.from_function_response(name=name, response={"error": "Hands failed to execute any tool."})
                            )
                    except Exception as e:
                        previous_function_responses.append(
                            types.Part.from_function_response(name=name, response={"error": f"Hands Error: {str(e)}"})
                        )
                else:
                    # Execute Brain Tool Directly (shell_action, task_complete, etc.)
                    gen = self.executor.execute_tool(name, args, logical_width, logical_height, brain_thought)
                    while True:
                        try:
                            yielded_val = next(gen)
                            yield yielded_val
                        except StopIteration as e:
                            _, result_dict, is_finished, _ = e.value
                            if is_finished: task_finished = True
                            break
                            
                    previous_function_responses.append(
                        types.Part.from_function_response(name=name, response=result_dict)
                    )

            if task_finished:
                break
                
            self.bridge.wait(WAIT_TIME_SECONDS)
