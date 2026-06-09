from dataclasses import dataclass, field
from typing import List, Dict, Any
import time

@dataclass
class CLIState:
    global_tasks: List[Dict[str, Any]] = field(default_factory=list)
    logging_enabled: bool = True
    voice_enabled: bool = False
    paused: bool = False
    
    # Live metrics
    total_steps: int = 0
    api_calls: int = 0
    session_start_time: float = field(default_factory=time.time)
    estimated_cost: float = 0.0
    
    # Agent loop detection
    last_action_signature: str = ""
    consecutive_same_action: int = 0
    consecutive_popup_mentions: int = 0
    
    # Session action history (for /history command)
    session_actions: List[Dict[str, Any]] = field(default_factory=list)
    
    def clear_tasks(self):
        self.global_tasks.clear()
        
    def add_task(self, task_desc: str):
        self.global_tasks.append({"desc": task_desc, "status": "pending"})
        
    def record_action(self, action_name: str, args: dict, thought: str = ""):
        """Record an action for /history and loop detection."""
        import time as _time
        self.total_steps += 1
        
        entry = {
            "step": self.total_steps,
            "time": _time.time(),
            "action": action_name,
            "args": args,
            "thought": thought,
        }
        self.session_actions.append(entry)
        if len(self.session_actions) > 100:
            self.session_actions.pop(0)
        
        # Loop detection: build a signature from action + key args
        sig = f"{action_name}:{_simplify_args(args)}"
        if sig == self.last_action_signature:
            self.consecutive_same_action += 1
        else:
            self.consecutive_same_action = 0
            self.last_action_signature = sig
            
        # Popup mention detection
        thought_lower = (thought or "").lower()
        if any(kw in thought_lower for kw in ["popup", "dialog", "modal", "overlay", "dismiss", "close this"]):
            self.consecutive_popup_mentions += 1
        else:
            self.consecutive_popup_mentions = 0
    
    def record_api_call(self):
        from core.config import COST_PER_API_CALL
        self.api_calls += 1
        self.estimated_cost += COST_PER_API_CALL
        
    def get_elapsed(self) -> str:
        elapsed = time.time() - self.session_start_time
        m, s = divmod(int(elapsed), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}h {m}m {s}s"
        elif m > 0:
            return f"{m}m {s}s"
        return f"{s}s"


def _simplify_args(args: dict) -> str:
    """Create a simplified string signature of tool args for loop detection."""
    if not args:
        return ""
    # For mouse actions, include action + rough coordinates
    if "x" in args and "y" in args:
        return f"{args.get('action', '')}@{args.get('x', 0)},{args.get('y', 0)}"
    if "command" in args:
        return args["command"][:50]
    if "text" in args:
        return args["text"][:30]
    if "keys" in args:
        return str(args["keys"])
    return str(args)[:40]
