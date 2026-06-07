from google.genai import types

def get_tools():
    custom_function_declarations = [
        {
            "name": "mouse_action",
            "description": "Perform a mouse action on the screen.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "action": {
                        "type": "STRING",
                        "description": "One of: click, double_click, right_click, move, drag"
                    },
                    "x": {
                        "type": "INTEGER",
                        "description": "X coordinate scaled from 0 to 1000, where 1000 is the right edge of the screen."
                    },
                    "y": {
                        "type": "INTEGER",
                        "description": "Y coordinate scaled from 0 to 1000, where 1000 is the bottom edge of the screen."
                    }
                },
                "required": ["action", "x", "y"]
            }
        },
        {
            "name": "keyboard_action",
            "description": "Perform a keyboard action.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "action": {
                        "type": "STRING",
                        "description": "One of: type, press"
                    },
                    "text": {
                        "type": "STRING",
                        "description": "Text to type if action is 'type'"
                    },
                    "keys": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": "Keys to press if action is 'press' (e.g., ['command', 'space'])"
                    }
                },
                "required": ["action"]
            }
        },
        {
            "name": "shell_action",
            "description": "Execute a shell command. Use this heavily to quickly accomplish tasks (e.g., 'open -a Safari', 'osascript ...').",
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
            "name": "scroll_action",
            "description": "Scroll the screen. You MUST provide the x and y coordinates of the area you want to scroll.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "clicks": {
                        "type": "INTEGER",
                        "description": "Amount to scroll. Try positive values first. If the screen scrolls the wrong way, immediately try negative values."
                    },
                    "x": {
                        "type": "INTEGER",
                        "description": "X coordinate scaled from 0 to 1000 of the target area."
                    },
                    "y": {
                        "type": "INTEGER",
                        "description": "Y coordinate scaled from 0 to 1000 of the target area."
                    }
                },
                "required": ["clicks", "x", "y"]
            }
        },
        {
            "name": "wait_action",
            "description": "Explicitly wait for a number of seconds. Use this to wait for UI elements to load.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "seconds": {
                        "type": "INTEGER"
                    }
                },
                "required": ["seconds"]
            }
        },
        {
            "name": "task_complete",
            "description": "Call this when the task is fully completed or cannot proceed.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "status": {
                        "type": "STRING",
                        "description": "Brief final status message."
                    },
                    "report": {
                        "type": "STRING",
                        "description": "A comprehensive, detailed top-to-bottom summary of everything you did, the information you found, and the final results."
                    }
                },
                "required": ["status", "report"]
            }
        },
        {
            "name": "manage_tasks",
            "description": "Add, check off, or clear tasks from the Task Manager UI panel.",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "action": {
                        "type": "STRING",
                        "description": "One of: add, complete, clear"
                    },
                    "task_description": {
                        "type": "STRING",
                        "description": "Description of the task to add or complete."
                    }
                },
                "required": ["action"]
            }
        },
        {
            "name": "ask_human",
            "description": "Pause execution and ask the human user a question (e.g., for CAPTCHAs, passwords, or clarification on ambiguity).",
            "parameters": {
                "type": "OBJECT",
                "properties": {
                    "question": {
                        "type": "STRING",
                        "description": "The exact question to ask the user in the terminal."
                    }
                },
                "required": ["question"]
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
            function_declarations=custom_function_declarations
        )
    ]
