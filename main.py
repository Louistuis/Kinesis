import sys
import pyautogui
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.theme import Theme
from rich.rule import Rule
from rich.live import Live
from ui.dashboard import LiveDashboard
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.completion import WordCompleter
import warnings
import logging

warnings.filterwarnings("ignore")
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger("google.genai").setLevel(logging.CRITICAL)

from core.agent import MacAgent

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

    session = PromptSession(history=InMemoryHistory())
    
    # Prompt toolkit styling
    pt_style = Style.from_dict({
        'prompt': 'ansicyan bold',
        'bottom-toolbar': 'bg:#222222 #aaaaaa',
    })

    def bottom_toolbar():
        return HTML(' <b>Kinesis CLI</b> • Autonomous Agent • Press Ctrl+C to abort task • Type /help for commands ')

    slash_commands = {
        "/help": "Show available commands",
        "/exit": "Exit Kinesis CLI",
        "/quit": "Exit Kinesis CLI",
        "/clear": "Clear the terminal screen",
        "/status": "Show agent status and system info",
        "/update": "Pull latest code and instantly hot-reload Kinesis",
    }
    completer = WordCompleter(list(slash_commands.keys()), ignore_case=True)

    while True:
        try:
            # Separation rule for new task
            console.print("\n", Rule(style="cyan"))
            task = session.prompt("\n🚀 DIRECTIVE > ", style=pt_style, bottom_toolbar=bottom_toolbar, completer=completer)
            cmd = task.lower().strip()
            
            if cmd in ['/exit', '/quit', 'exit', 'quit']:
                console.print("[dim]Exiting Kinesis CLI... Goodbye.[/dim]")
                break
            if cmd == '/clear':
                import os
                os.system('clear')
                console.clear()
                continue
            if cmd == '/help':
                help_text = "**Available Slash Commands:**\n\n"
                for k, v in slash_commands.items():
                    help_text += f"- `{k}`: {v}\n"
                console.print(Panel(Markdown(help_text), border_style="blue"))
                continue
            if cmd == '/status':
                width, height = pyautogui.size()
                status_text = f"**System Information:**\n- Primary Display Resolution: {width}x{height}\n- Fail-Safe: Active\n- API Model: gemini-2.5-computer-use-preview-10-2025"
                console.print(Panel(Markdown(status_text), border_style="magenta"))
                continue
            if cmd == '/update':
                console.print("\n[dim]Pulling latest changes from GitHub...[/dim]")
                import subprocess
                subprocess.run(["git", "pull", "origin", "master"])
                console.print("[bold green]Update complete. Hot-reloading Kinesis...[/bold green]")
                # Kill background phantom cursor process
                try:
                    cursor_process.terminate()
                except:
                    pass
                # Physically replace current python process with a new one
                import os
                os.execv(sys.executable, [sys.executable, __file__])
                
            if not task.strip():
                continue
                
            
            dashboard = LiveDashboard(task)
            step_counter = 1
            
            import time
            def get_renderable():
                dashboard.spinner.render(time.time()) # tick spinner
                return dashboard.build_layout()
            
            try:
                with Live(get_renderable(), console=console, refresh_per_second=15) as live:
                    for event in agent.run(task):
                        if event["type"] == "status" or event["type"] == "info":
                            dashboard.update_status(event['message'])
                            
                        elif event["type"] == "action":
                            thought = event.get('thought')
                            if thought:
                                dashboard.update_thought(thought)
                                
                            action_name = event['action_name']
                            args = event['args']
                            
                            if action_name == "mouse_action":
                                icon = "🖱️ "
                                desc = f"[bold green]{args.get('action').upper()}[/bold green]"
                                target = f"Model: ({args.get('x')}, {args.get('y')})"
                                if event.get('native_coords'):
                                    target += f" ➡️  [bold yellow]Native: {event['native_coords']}[/bold yellow]"
                            elif action_name == "keyboard_action":
                                icon = "⌨️ "
                                desc = f"[bold green]{args.get('action').upper()}[/bold green]"
                                target = f"Text: '{args.get('text', '')}' | Keys: {args.get('keys', [])}"
                            elif action_name == "shell_action":
                                icon = "🐚 "
                                desc = f"[bold green]EXECUTE SHELL[/bold green]"
                                target = f"[dim]{args.get('command', '')}[/dim]"
                            elif action_name == "scroll_action":
                                icon = "🖱️ "
                                desc = f"[bold green]SCROLL[/bold green]"
                                target = f"Clicks: {args.get('clicks', 0)}"
                            elif action_name == "wait_action":
                                icon = "⏳ "
                                desc = f"[bold green]WAIT[/bold green]"
                                target = f"{args.get('seconds', 2)} seconds"
                            else:
                                icon = "⚙️ "
                                desc = f"[bold green]{action_name}[/bold green]"
                                target = str(args)
                                
                            dashboard.add_action(step_counter, icon, desc, target)
                            step_counter += 1
                            
                        elif event["type"] == "complete":
                            thought = event.get('thought')
                            if thought:
                                dashboard.update_thought(thought)
                            dashboard.update_status(f"✅ TASK COMPLETE: {event.get('status')}")
                            live.update(dashboard.build_layout())
                            time.sleep(1) # Let the user see completion before closing Live
                            console.print(Panel(f"✅ [bold green]TASK COMPLETE:[/bold green] {event.get('status')}", border_style="green", padding=(1, 2)))
                            
                        elif event["type"] == "error":
                            dashboard.update_status(f"❌ ERROR: {event['message']}")
                            live.update(dashboard.build_layout())
                            time.sleep(1)
                            console.print(Panel(f"❌ [bold red]ERROR:[/bold red] {event['message']}", border_style="red"))
                            
                        # Continually update the UI frame
                        live.update(get_renderable())
                        
            finally:
                pass
                
        except pyautogui.FailSafeException:
            console.print("\n[bold red][FAIL-SAFE TRIGGERED] Mouse moved to screen corner. Execution aggressively aborted.[/bold red]")
        except KeyboardInterrupt:
            # We catch interrupt here so the user can abort a task cleanly
            console.print("\n[warning]Task interrupted.[/warning]")
        except EOFError:
            break
        except Exception as e:
            console.print(f"\n[danger]Critical Error:[/danger] {e}")

if __name__ == "__main__":
    main()
