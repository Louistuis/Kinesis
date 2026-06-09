from google.genai import types

def get_brain_tools():
    """Tools for the Reasoning Model (Brain)."""
    return [
        types.Tool(
            function_declarations=[
                {
                    "name": "handoff_action",
                    "description": "Send a physical execution instruction to your Hands (the computer-use model).",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "instruction": {
                                "type": "STRING",
                                "description": "Specific, clear instructions of what to click, type, or scroll. (e.g., 'Click the blue login button', 'Type hello world')."
                            }
                        },
                        "required": ["instruction"]
                    }
                },
                {
                    "name": "shell_action",
                    "description": "Execute a shell command.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "command": {
                                "type": "STRING",
                                "description": "The shell command to execute."
                            }
                        },
                        "required": ["command"]
                    }
                },
                {
                    "name": "wait_action",
                    "description": "Pause execution.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "seconds": {
                                "type": "INTEGER",
                                "description": "Number of seconds to wait."
                            }
                        },
                        "required": ["seconds"]
                    }
                },
                {
                    "name": "task_complete",
                    "description": "Call this ONLY when the entire user directive has been successfully completed.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "status": {
                                "type": "STRING",
                                "description": "Brief final status message."
                            },
                            "report": {
                                "type": "STRING",
                                "description": "A comprehensive, detailed top-to-bottom summary."
                            }
                        },
                        "required": ["status", "report"]
                    }
                },
                {
                    "name": "ask_human",
                    "description": "Pause execution and ask the human user a question.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "question": {
                                "type": "STRING",
                                "description": "The exact question to ask the user."
                            }
                        },
                        "required": ["question"]
                    }
                }
            ]
        )
    ]

def get_hands_tools():
    """Tools for the Execution Model (Hands)."""
    custom_declarations = [
        {
            "name": "mouse_action",
            "description": "Fallback mouse action if native fails.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "action": {"type": "STRING", "description": "click, drag, etc"},
                    "x": {"type": "INTEGER"},
                    "y": {"type": "INTEGER"}
                },
                "required": ["action", "x", "y"]
            }
        },
        {
            "name": "keyboard_action",
            "description": "Fallback keyboard action if native fails.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "action": {"type": "STRING", "description": "type, press"},
                    "text": {"type": "STRING"},
                    "keys": {"type": "ARRAY", "items": {"type": "STRING"}}
                },
                "required": ["action"]
            }
        },
        {
            "name": "scroll_action",
            "description": "Fallback scroll action.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "clicks": {"type": "INTEGER"},
                    "x": {"type": "INTEGER"},
                    "y": {"type": "INTEGER"}
                },
                "required": ["clicks"]
            }
        }
    ]
    
    return [
        types.Tool(
            computer_use=types.ComputerUse(
                environment=types.Environment.ENVIRONMENT_DESKTOP
            )
        ),
        types.Tool(
            function_declarations=custom_declarations
        )
    ]
