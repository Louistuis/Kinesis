from core.config import model_to_native_coords

class ActionExecutor:
    def __init__(self, bridge):
        self.bridge = bridge

    def execute_tool(self, name, args, logical_width, logical_height, response_text):
        """Executes a single tool and yields events/results."""
        event = {
            "type": "action",
            "action_name": name,
            "args": args,
            "thought": response_text.strip() if response_text else None,
            "native_coords": None
        }
        
        result_dict = {"status": "success", "url": "http://localhost"}
        task_finished = False
        action_executed = False
        
        try:
            if name == "mouse_action" or name == "computer_use":
                if name == "computer_use":
                    action = args.get("action")
                    if action == "left_click": action = "click"
                    elif action == "left_click_drag": action = "drag"
                    elif action == "mouse_move": action = "move"
                    
                    coords = args.get("coordinates")
                    if coords:
                        x_model, y_model = coords
                    else:
                        x_model, y_model = 0, 0
                        
                    if action == "type":
                        yield event
                        self.bridge.execute_keyboard_action("type", text=args.get("text", ""))
                        action_executed = True
                        return event, result_dict, task_finished, action_executed
                else:
                    x_model = int(args["x"])
                    y_model = int(args["y"])
                    action = args["action"]
                    
                x_native, y_native = model_to_native_coords(x_model, y_model, logical_width, logical_height)
                event["native_coords"] = (x_native, y_native)
                
                yield event
                self.bridge.execute_mouse_action(action, x_native, y_native)
                action_executed = True
                
            elif name == "keyboard_action":
                yield event
                self.bridge.execute_keyboard_action(args["action"], args.get("text", ""), args.get("keys", []))
                action_executed = True
                
            elif name == "shell_action":
                command = args.get("command", "")
                yield event
                output = self.bridge.execute_shell_action(command)
                result_dict["output"] = output
                yield {"type": "info", "message": f"Shell output: {output[:500]}..."}
                action_executed = True
                
            elif name == "scroll_action":
                yield event
                self.bridge.execute_scroll_action(int(args.get("clicks", 0)))
                action_executed = True
                
            elif name == "wait_action":
                yield event
                self.bridge.wait(int(args.get("seconds", 2)))
                action_executed = True
                
            elif name == "task_complete":
                status = args.get("status", "Completed")
                result_dict["status"] = status
                yield {"type": "complete", "status": status, "thought": event["thought"]}
                task_finished = True
                action_executed = True
                
            elif name in ["click_at", "type_text_at"]:
                x_model = int(args.get("x", 0))
                y_model = int(args.get("y", 0))
                
                x_native, y_native = model_to_native_coords(x_model, y_model, logical_width, logical_height)
                event["native_coords"] = (x_native, y_native)
                
                yield event
                self.bridge.execute_mouse_action("click", x_native, y_native)
                
                if name == "type_text_at":
                    text = args.get("text", "")
                    self.bridge.execute_keyboard_action("type", text=text)
                    
                action_executed = True
                
            elif name == "scroll_document":
                yield event
                
                # The schema might pass 'direction' instead of amount
                direction = args.get("direction", "down")
                clicks = int(args.get("amount", args.get("clicks", 1000)))
                
                # If direction is down, scroll amount should be negative (on most macOS setups)
                if direction == "down":
                    clicks = -abs(clicks)
                elif direction == "up":
                    clicks = abs(clicks)
                
                # macOS PyAutoGUI scroll is in pixels, so '1' is nothing.
                # If the AI passed '1' (e.g. 1 click), we multiply it by 500 to scroll a page.
                if abs(clicks) < 10:
                    clicks *= 500
                    
                self.bridge.execute_scroll_action(clicks)
                action_executed = True
                
            elif name in ["wait", "wait_5_seconds"]:
                yield event
                seconds = int(args.get("seconds", 5))
                self.bridge.wait(seconds)
                action_executed = True
                
            elif name == "key_combination":
                yield event
                # Depending on the schema, keys might be 'key', 'keys', or 'text'
                key = args.get("key", args.get("keys", args.get("text", "")))
                if isinstance(key, list):
                    self.bridge.execute_keyboard_action("press", keys=key)
                else:
                    self.bridge.execute_keyboard_action("press", keys=[str(key)])
                action_executed = True
                
            else:
                error_msg = f"Unknown tool called: {name}. You MUST use only the provided tools (mouse_action, shell_action, etc.). Do NOT use {name}."
                yield {"type": "error", "message": error_msg}
                result_dict["error"] = error_msg
                action_executed = True # count as executed so it waits
                
        except Exception as e:
            yield {"type": "error", "message": f"Error executing {name}: {e}"}
            result_dict["error"] = str(e)
            
        return event, result_dict, task_finished, action_executed
