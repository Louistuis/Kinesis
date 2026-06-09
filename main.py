import sys
import time
import pyautogui
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.theme import Theme
from rich.text import Text
from rich.rule import Rule
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

BANNER_LINES = [
    ("██╗  ██╗██╗███╗   ██╗███████╗███████╗██╗███████╗", "bold magenta"),
    ("██║ ██╔╝██║████╗  ██║██╔════╝██╔════╝██║██╔════╝", "bold magenta"),
    ("█████╔╝ ██║██╔██╗ ██║█████╗  ███████╗██║███████╗", "bold cyan"),
    ("██╔═██╗ ██║██║╚██╗██║██╔══╝  ╚════██║██║╚════██║", "bold cyan"),
    ("██║  ██╗██║██║ ╚████║███████╗███████║██║███████║", "bold blue"),
    ("╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝╚═╝╚══════╝", "bold blue"),
]

def print_banner(console: Console):
    """Print the gradient ASCII art banner."""
    console.print()
    for line, style in BANNER_LINES:
        console.print(f"  [{style}]{line}[/{style}]")
    console.print()
    console.print()

def boot_check(console: Console, label: str, detail: str, success: bool = True):
    """Print a single boot check line with staggered animation."""
    time.sleep(0.12)
    icon = "[bold green]✓[/bold green]" if success else "[bold red]✗[/bold red]"
    console.print(f"  {icon} [bold white]{label:<24}[/bold white] [dim]— {detail}[/dim]")

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
    
    # ── Premium Boot Sequence ──────────────────────────────────
    os.system('clear')
    print_banner(console)
    from core.config import MODEL_NAME, KINESIS_VERSION, GEMINI_AUTH_MODE
    console.print(f"  [dim]v{KINESIS_VERSION} • Autonomous macOS Computer-Use Agent • Powered by Gemini 3 Flash[/dim]")
    console.print()
    console.print(Rule(style="dim blue"))
    console.print()
    
    # Boot checks with staggered animation
    
    auth_label = "OAuth / ADC" if GEMINI_AUTH_MODE == "oauth" else "API Key"
    boot_check(console, "Authentication", f"{auth_label} → {MODEL_NAME}")
    
    # Screen Recording check
    try:
        from PIL import ImageGrab
        ImageGrab.grab(bbox=(0, 0, 10, 10))
        boot_check(console, "Screen Recording", "Permissions OK")
    except Exception:
        boot_check(console, "Screen Recording", "MISSING — grant in System Settings!", success=False)
    
    from core.mac_os_bridge import MacBridge
    import subprocess
    import os
    
    bridge = MacBridge()
    screens = bridge.get_screens()
    
    # Spawn Phantom Cursor
    cursor_process = subprocess.Popen([sys.executable, "ui/cursor.py"], cwd=os.path.dirname(os.path.abspath(__file__)))
    boot_check(console, "Phantom Cursor", "Spawned")
    
    # Screen selection
    if len(screens) > 1:
        overlay_args = [sys.executable, "ui/overlay.py"]
        for s in screens:
            overlay_args.extend([str(s["appkit_x"]), str(s["appkit_y"]), str(s["w"]), str(s["h"]), str(s["index"])])
            
        subprocess.Popen(overlay_args, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        for i, s in enumerate(screens):
            boot_check(console, f"Display {i+1}", f"{s['w']}x{s['h']}")
        
        console.print()
        console.print(f"  [bold magenta]Multiple monitors detected ({len(screens)}).[/bold magenta]")
        while True:
            choice = input(f"  Which screen should Kinesis operate on? (1-{len(screens)}) > ").strip()
            try:
                idx = int(choice)
                if 1 <= idx <= len(screens):
                    selected_screen = screens[idx-1]
                    bridge.set_active_screen((selected_screen["x"], selected_screen["y"], selected_screen["w"], selected_screen["h"]))
                    console.print(f"  [dim]Screen {idx} selected.[/dim]")
                    break
                else:
                    console.print("  [danger]Invalid selection.[/danger]")
            except:
                console.print("  [danger]Please enter a valid number.[/danger]")
    else:
        bridge.set_active_screen((screens[0]["x"], screens[0]["y"], screens[0]["w"], screens[0]["h"]))
        boot_check(console, "Display", f"{screens[0]['w']}x{screens[0]['h']} (Screen 1)")

    boot_check(console, "Fail-Safe", "Active (corner abort)")
    boot_check(console, "Mission Saving", "Enabled")
    
    console.print()
    console.print(Rule(style="dim blue"))
    console.print()
    console.print("  [bold green]System ready.[/bold green] [dim]Type a directive or /help for commands.[/dim]")

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
