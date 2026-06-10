import threading
import json
from google import genai
from core.config import GEMINI_API_KEY, GEMINI_AUTH_MODE

class TaskObserver:
    def __init__(self, directive: str, global_tasks: list, dashboard):
        self.directive = directive
        self.global_tasks = global_tasks
        self.dashboard = dashboard
        from core.config import get_genai_client
        self.client = get_genai_client()
        self.model_name = "gemini-3.1-flash-lite-preview"
        self._lock = threading.Lock()
        
    def _parse_tasks(self, text: str) -> list:
        try:
            # Try to find JSON array in the text
            start = text.find('[')
            end = text.rfind(']') + 1
            if start != -1 and end != 0:
                return json.loads(text[start:end])
            return []
        except:
            return []

    def initialize_tasks_async(self):
        """Generates the initial exhaustive checklist in the background."""
        def run():
            prompt = (
                f"You are the internal Task Manager for an autonomous AI agent.\n"
                f"The agent was given this directive: '{self.directive}'\n\n"
                f"Break this directive down into an EXHAUSTIVE, granular, step-by-step checklist of micro-tasks.\n"
                f"You MUST generate at least 5 to 10 distinct, highly granular steps.\n"
                f"Output exactly a JSON array of strings representing the tasks. Nothing else.\n"
                f"Example: [\"Open Spotlight search\", \"Search for 'System Settings'\", \"Click to open System Settings\", \"Click on 'Displays' in the sidebar\", \"Locate the resolution scaling options\", \"Set resolution to Default\"]\n"
            )
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                tasks = self._parse_tasks(response.text)
                with self._lock:
                    for t in tasks:
                        self.global_tasks.append({"desc": t, "status": "pending"})
                        self.dashboard.add_task(t)
            except Exception as e:
                pass # Fail silently, tasks remain empty
                
        threading.Thread(target=run, daemon=True).start()

    def update_tasks_async(self, recent_thought: str, recent_action: str, recent_target: str):
        """Dynamically checks off tasks or adds new ones based on agent progress."""
        if not self.global_tasks:
            return
            
        def run():
            with self._lock:
                current_tasks = [{"desc": t["desc"], "status": t["status"]} for t in self.global_tasks]
                
            prompt = (
                f"You are the internal Task Manager for an autonomous AI agent.\n"
                f"Directive: '{self.directive}'\n\n"
                f"Current Task List:\n{json.dumps(current_tasks, indent=2)}\n\n"
                f"The agent just thought: '{recent_thought}'\n"
                f"The agent just executed action: '{recent_action}' on target '{recent_target}'.\n\n"
                f"Analyze the agent's progress. Has it completed any pending tasks? Has it discovered new steps that need to be added?\n"
                f"CRITICAL: If the agent explicitly states in its thought that it is STUCK IN A LOOP or wants to skip a popup/roadblock, YOU MUST IMMEDIATELY delete the blocked tasks and generate an alternative task list to bypass the roadblock.\n"
                f"Update the 'status' of completed tasks to 'completed'. Add new tasks as dictionaries with 'desc' and 'status'='pending' if needed.\n"
                f"Output exactly the updated JSON array of task objects. Nothing else."
            )
            
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                updated_tasks = self._parse_tasks(response.text)
                if updated_tasks:
                    with self._lock:
                        self.global_tasks.clear()
                        self.dashboard.clear_tasks()
                        for t in updated_tasks:
                            desc = t.get("desc", "")
                            status = t.get("status", "pending")
                            if desc:
                                self.global_tasks.append({"desc": desc, "status": status})
                                self.dashboard.add_task(desc)
                                if status == "completed":
                                    self.dashboard.complete_task(desc)
            except Exception:
                pass
                
        threading.Thread(target=run, daemon=True).start()
