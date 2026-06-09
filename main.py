import sys
import pyautogui
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.theme import Theme
import warnings
import logging

warnings.filterwarnings("ignore")
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger("google.genai").setLevel(logging.CRITICAL)

from core.agent import MacAgent
from core.cli import KinesisCLI

# Custom premium theme
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red"
})

def main():
    import os
    from dotenv import load_dotenv
    
    # Check for setup wizard
    setup_marker = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".setup_complete")
    if not os.path.exists(setup_marker):
        from ui import wizard
        wizard.run_setup_wizard()
        
    # Load env vars after potential wizard setup
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
    
    console = Console(theme=custom_theme)
    
    welcome_text = """
# **Kinesis CLI**
### Autonomous macOS Computer-Use Agent

*System initialized. Awaiting natural language directives or slash commands.*
> [!WARNING]
> Global Fail-Safe is ACTIVE. Move mouse to any screen corner to abort immediately.
"""
    console.print(Panel(Markdown(welcome_text), border_style="cyan", padding=(1, 2)))
    
    from core.mac_os_bridge import MacBridge
    import subprocess
    import os
    
    bridge = MacBridge()
    screens = bridge.get_screens()
    
    if len(screens) > 1:
        overlay_args = [sys.executable, "ui/overlay.py"]
        for s in screens:
            overlay_args.extend([str(s["appkit_x"]), str(s["appkit_y"]), str(s["w"]), str(s["h"]), str(s["index"])])
            
        subprocess.Popen(overlay_args, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        console.print(f"\n[bold magenta]Multiple monitors detected ({len(screens)}).[/bold magenta]")
        while True:
            choice = input(f"Which screen would you like Kinesis to operate on? (1-{len(screens)}) > ").strip()
            try:
                idx = int(choice)
                if 1 <= idx <= len(screens):
                    selected_screen = screens[idx-1]
                    bridge.set_active_screen((selected_screen["x"], selected_screen["y"], selected_screen["w"], selected_screen["h"]))
                    console.print(f"[dim]Screen {idx} selected.[/dim]")
                    break
                else:
                    console.print("[danger]Invalid selection. Please enter a valid screen number.[/danger]")
            except:
                console.print("[danger]Please enter a valid number.[/danger]")
    else:
        bridge.set_active_screen((screens[0]["x"], screens[0]["y"], screens[0]["w"], screens[0]["h"]))

    # Spawn Phantom Cursor
    cursor_process = subprocess.Popen([sys.executable, "ui/cursor.py"], cwd=os.path.dirname(os.path.abspath(__file__)))

    import atexit
    def cleanup():
        try:
            cursor_process.terminate()
        except:
            pass
    atexit.register(cleanup)

    try:
        agent = MacAgent(bridge=bridge)
    except Exception as e:
        console.print(f"[danger]Initialization Error:[/danger] {e}")
        console.print("Please ensure GEMINI_API_KEY environment variable is set.")
        sys.exit(1)

    # Boot the refactored CLI loop
    cli = KinesisCLI(console, agent, cursor_process)
    cli.start()

if __name__ == "__main__":
    main()
