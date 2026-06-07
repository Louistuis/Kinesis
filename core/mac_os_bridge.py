import pyautogui
from PIL import ImageGrab, Image
import time
import subprocess
import Quartz
from core.config import calculate_scaling_factor, TARGET_MAX_WIDTH

# Global Fail-Safe: Moving mouse to any corner will abort execution
pyautogui.FAILSAFE = True

class MacBridge:
    def __init__(self):
        self.active_screen_bbox = None  # (x, y, w, h)
        self.logical_width, self.logical_height = pyautogui.size()
        self.human_response = None

    def get_screens(self) -> list[dict]:
        """Returns a list of connected screens with their logical bounding boxes."""
        try:
            import AppKit
            screens = AppKit.NSScreen.screens()
            primary_h = screens[0].frame().size.height
            
            screen_list = []
            for i, s in enumerate(screens):
                f = s.frame()
                x_appkit = f.origin.x
                y_appkit = f.origin.y
                w = f.size.width
                h = f.size.height
                
                # Convert AppKit coordinates (bottom-left origin) to PyAutoGUI/Pillow coordinates (top-left origin)
                py_x = int(x_appkit)
                py_y = int(primary_h - (y_appkit + h))
                py_w = int(w)
                py_h = int(h)
                
                screen_list.append({
                    "index": i + 1,
                    "x": py_x,
                    "y": py_y,
                    "w": py_w,
                    "h": py_h,
                    "appkit_x": x_appkit,
                    "appkit_y": y_appkit
                })
            return screen_list
        except ImportError:
            # Fallback to pyautogui single screen
            w, h = pyautogui.size()
            return [{"index": 1, "x": 0, "y": 0, "w": w, "h": h, "appkit_x": 0, "appkit_y": 0}]

    def set_active_screen(self, bbox: tuple[int, int, int, int]):
        self.active_screen_bbox = bbox
        self.logical_width = bbox[2]
        self.logical_height = bbox[3]

    def focus_active_screen(self):
        """Silently clicks the menu bar of the active screen to shift macOS focus."""
        if self.active_screen_bbox:
            # Menu bar is at the top of the screen. We click y+5, x+width/2
            safe_x = self.active_screen_bbox[0] + (self.active_screen_bbox[2] // 2)
            safe_y = self.active_screen_bbox[1] + 5
            
            # Save current mouse position to restore it if needed? No, just move.
            pyautogui.moveTo(safe_x, safe_y, duration=0.0)
            pyautogui.click(button='left')
            time.sleep(0.1)

    def capture_screen(self) -> tuple[Image.Image, int, int]:
        """Captures screen, resizes, and returns image + scaling factor for PyAutoGUI."""
        # Grab screen
        try:
            if self.active_screen_bbox:
                # bbox takes (left, top, right, bottom)
                left = self.active_screen_bbox[0]
                top = self.active_screen_bbox[1]
                right = left + self.active_screen_bbox[2]
                bottom = top + self.active_screen_bbox[3]
                screenshot = ImageGrab.grab(bbox=(left, top, right, bottom), all_screens=True)
            else:
                screenshot = ImageGrab.grab(all_screens=True)
                
            physical_width, physical_height = screenshot.size
            logical_width, logical_height = self.logical_width, self.logical_height
        except Exception as e:
            raise RuntimeError(
                f"Failed to capture screen ({e}).\n"
                "Please ensure your Terminal has 'Screen Recording' permissions enabled "
                "in macOS System Settings -> Privacy & Security -> Screen Recording."
            )

        
        # Calculate scaling factor for resizing the physical image
        image_scaling_factor = calculate_scaling_factor(physical_width, TARGET_MAX_WIDTH)
        
        # Scale if necessary
        if image_scaling_factor < 1.0:
            new_width = int(physical_width * image_scaling_factor)
            new_height = int(physical_height * image_scaling_factor)
            screenshot = screenshot.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
        # We now use normalized 1000x1000 scaling for Gemini 2.5
        return screenshot, logical_width, logical_height

    def execute_mouse_action(self, action: str, x: int, y: int):
        """Executes phantom mouse action. Coordinates should be NATIVE."""
        # Offset coordinates to the selected screen's bounding box
        if self.active_screen_bbox:
            x += self.active_screen_bbox[0]
            y += self.active_screen_bbox[1]
            
        # 1. Update visual Kinesis cursor overlay
        try:
            import json
            with open('cursor_pos.txt', 'w') as f:
                f.write(json.dumps({"state": "moving", "x": x, "y": y}))
        except Exception:
            pass
            
        # 2. Phantom Execution (CoreGraphics instantaneous warp)
        import Quartz
        
        # Save current physical mouse position
        event = Quartz.CGEventCreate(None)
        current_pos = Quartz.CGEventGetLocation(event)
        
        # Warp to AI target silently
        target_pos = (float(x), float(y))
        
        if action == "move":
            move_event = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, target_pos, 0)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, move_event)
            # Sleep 0.05 to let hover register before warping back
            time.sleep(0.05)
            
        elif action in ["click", "double_click", "right_click"]:
            try:
                import json
                with open('cursor_pos.txt', 'w') as f:
                    f.write(json.dumps({"state": "clicking", "x": x, "y": y}))
            except: pass
            
            if action == "click":
                click_down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, target_pos, Quartz.kCGMouseButtonLeft)
                click_up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, target_pos, Quartz.kCGMouseButtonLeft)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_down)
                time.sleep(0.01)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_up)
            elif action == "double_click":
                click_down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, target_pos, Quartz.kCGMouseButtonLeft)
                click_up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, target_pos, Quartz.kCGMouseButtonLeft)
                Quartz.CGEventSetIntegerValueField(click_down, Quartz.kCGMouseEventClickState, 2)
                Quartz.CGEventSetIntegerValueField(click_up, Quartz.kCGMouseEventClickState, 2)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_down)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_up)
            elif action == "right_click":
                click_down = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventRightMouseDown, target_pos, Quartz.kCGMouseButtonRight)
                click_up = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventRightMouseUp, target_pos, Quartz.kCGMouseButtonRight)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_down)
                time.sleep(0.01)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, click_up)
            
        elif action == "drag":
            # Drag is harder to phantom. We will use PyAutoGUI for drag and let it steal the mouse briefly.
            pyautogui.moveTo(current_pos.x, current_pos.y, duration=0.0)
            pyautogui.dragTo(x, y, duration=0.5, button='left')
            current_pos = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None)) # don't warp back after drag

        # Instantly restore hardware mouse position
        if action != "drag":
            restore_event = Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventMouseMoved, current_pos, 0)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, restore_event)

    def execute_keyboard_action(self, action: str, text: str = "", keys: list[str] = None):
        """Executes native keyboard action."""
        if action == "type":
            if text:
                pyautogui.write(text, interval=0.05)
        elif action == "press":
            if keys:
                # e.g., keys=['command', 'space']
                pyautogui.hotkey(*keys)

    def execute_scroll_action(self, clicks: int):
        """Scrolls the screen by the specified amount. Positive=Up, Negative=Down."""
        # macOS scroll direction might be inverted depending on user settings. 
        # Typically, positive values scroll up, negative scroll down.
        # We animate the scroll line-by-line to simulate human trackpad inertia and bypass velocity limits.
        steps = abs(clicks)
        if steps == 0:
            return
            
        sleep_interval = 0.015
        direction = 1 if clicks > 0 else -1
        
        for _ in range(steps):
            pyautogui.scroll(direction)
            time.sleep(sleep_interval)
            
    def wait(self, seconds: float = 1.5):
        """Wait for UI render."""
        time.sleep(seconds)

    def execute_shell_action(self, command: str) -> str:
        """Executes a native shell command and returns output."""
        try:
            # If the command is trying to open an application, we MUST focus the target screen
            # first so macOS spawns the application on the correct monitor.
            if "open " in command or "open -a" in command:
                self.focus_active_screen()
                
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            out = ""
            if stdout: out += f"STDOUT:\n{stdout}\n"
            if stderr: out += f"STDERR:\n{stderr}\n"
            if not out: out = "Command executed successfully with no output."
            return out
        except Exception as e:
            return f"Command execution failed: {e}"
