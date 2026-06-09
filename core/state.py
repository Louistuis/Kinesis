from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class CLIState:
    global_tasks: List[Dict[str, Any]] = field(default_factory=list)
    logging_enabled: bool = False
    voice_enabled: bool = False
    
    def clear_tasks(self):
        self.global_tasks.clear()
        
    def add_task(self, task_desc: str):
        self.global_tasks.append({"desc": task_desc, "status": "pending"})
