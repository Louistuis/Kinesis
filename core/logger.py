import os
import json
import uuid
from datetime import datetime
from google import genai
from core.config import GEMINI_API_KEY

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")

class Logger:
    def __init__(self, directive: str):
        self.directive = directive
        self.actions = []
        self.thoughts = []
        self.id = uuid.uuid4().hex[:6]
        self.timestamp = datetime.now().isoformat()
        self.title = "Untitled Mission"
        
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR)
            
    def add_thought(self, thought: str):
        self.thoughts.append({
            "timestamp": datetime.now().isoformat(),
            "thought": thought
        })
        
    def add_action(self, action_name: str, args: dict):
        self.actions.append({
            "timestamp": datetime.now().isoformat(),
            "action": action_name,
            "args": args
        })
        
    def save(self):
        # Auto-name the conversation using Flash Lite
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = f"Summarize this desktop AI agent mission into a short, punchy 3-5 word title.\nDirective: {self.directive}\nActions Taken: {[a['action'] for a in self.actions]}\nOutput ONLY the title, no quotes or prefixes."
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=prompt
            )
            if response.text:
                self.title = response.text.strip().strip('"').strip()
        except Exception as e:
            self.title = f"Mission {self.id}"
            
        payload = {
            "id": self.id,
            "title": self.title,
            "timestamp": self.timestamp,
            "directive": self.directive,
            "thoughts": self.thoughts,
            "actions": self.actions
        }
        
        file_path = os.path.join(LOGS_DIR, f"{self.id}.json")
        with open(file_path, 'w') as f:
            json.dump(payload, f, indent=2)
            
        return self.id, self.title
