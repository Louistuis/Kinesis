import sys
import pyautogui
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.theme import Theme
from rich.live import Live
from rich.table import Table
from rich.rule import Rule
from ui.dashboard import LiveDashboard
from core.agent import MacAgent
from core.task_observer import TaskObserver
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
        "/clear": "Clear the terminal screen and agent memory",
        "/setup": "Restart the setup wizard to change API keys",
        "/status": "Show agent status and system info",
        "/version": "Show current Kinesis build version",
        "/update": "Pull latest code and instantly hot-reload Kinesis",
        "/tasks": "Inject tasks into the Task Manager (e.g., /tasks 'Find email', 'Reply')",
        "/list": "List all saved mission logs and results",
        "/log on": "Enable mission logging and AI auto-naming",
        "/log off": "Disable mission logging",
        "/log <id>": "View a specific mission log by ID",
        "/result <id>": "View the comprehensive final report of a mission",
        "/delete <id>": "Delete a mission log by ID or 'last'",
        "/resume <id>": "Resume a mission log by ID or 'last'",
    }
    completer = WordCompleter(list(slash_commands.keys()), ignore_case=True)

    global_tasks = []
    logging_enabled = False

    while True:
        try:
            # Separation rule for new task
            console.print("\n", Rule(style="cyan"))
            task = session.prompt("\n🚀 DIRECTIVE > ", style=pt_style, bottom_toolbar=bottom_toolbar, completer=completer)
            cmd = task.lower().strip()
            
            if cmd in ['/exit', '/quit', 'exit', 'quit']:
                console.print("[dim]Exiting Kinesis CLI... Goodbye.[/dim]")
                break
            if cmd == '/setup':
                import os
                setup_marker = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".setup_complete")
                if os.path.exists(setup_marker):
                    os.remove(setup_marker)
                console.print("\n[dim]Restarting Kinesis for Setup Wizard...[/dim]")
                try: cursor_process.terminate()
                except: pass
                os.execv(sys.executable, [sys.executable, __file__])
            if cmd == '/clear':
                import os
                os.system('clear')
                console.clear()
                agent.history = []
                global_tasks.clear()
                console.print("[dim]Terminal, agent memory, and task manager cleared.[/dim]")
                continue
            if task.lower().startswith('/log'):
                args = task.lower().split()
                if len(args) == 2 and args[1] == 'on':
                    logging_enabled = True
                    console.print("[bold green]Logging enabled.[/bold green]")
                elif len(args) == 2 and args[1] == 'off':
                    logging_enabled = False
                    console.print("[dim]Logging disabled.[/dim]")
                elif len(args) == 2:
                    log_id = args[1]
                    import os, json
                    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
                    log_file = os.path.join(logs_dir, f"{log_id}.json")
                    if os.path.exists(log_file):
                        with open(log_file, 'r') as f:
                            data = json.load(f)
                            console.print(f"\n[bold cyan]🧠 Mission: {data.get('title', 'Unknown')} ({data.get('id')})[/bold cyan]")
                            console.print(f"[dim italic]Directive: {data.get('directive', '')}[/dim italic]\n")
                            for i, act in enumerate(data.get('actions', [])):
                                console.print(f"  [bold magenta]{i+1}.[/bold magenta] {act.get('action').upper()}: {act.get('args')}")
                            console.print("\n")
                    else:
                        console.print(f"[bold red]Log {log_id} not found.[/bold red]")
                else:
                    console.print("[dim]Usage: /log on | /log off | /log [ID][/dim]")
                continue
            if cmd == '/list':
                import os, json
                from rich.table import Table
                logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
                if not os.path.exists(logs_dir) or not os.listdir(logs_dir):
                    console.print("[dim]No missions found.[/dim]")
                    continue
                table = Table(title="Mission History", show_header=True, header_style="bold magenta")
                table.add_column("ID", style="cyan")
                table.add_column("Title", style="green")
                table.add_column("Timestamp", style="dim")
                logs = []
                for f in os.listdir(logs_dir):
                    if f.endswith('.json'):
                        with open(os.path.join(logs_dir, f), 'r') as log_file:
                            try:
                                logs.append(json.load(log_file))
                            except:
                                pass
                logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                for log in logs:
                    table.add_row(log.get('id', ''), log.get('title', ''), log.get('timestamp', '')[:16].replace('T', ' '))
                console.print(table)
                continue
            if task.lower().startswith('/result '):
                args = task.lower().split()
                if len(args) == 2:
                    arg = args[1]
                    import os, json
                    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
                    target_file = None
                    if arg == 'last':
                        files = [f for f in os.listdir(logs_dir) if f.endswith('.json')]
                        if files:
                            files.sort(key=lambda x: os.path.getmtime(os.path.join(logs_dir, x)), reverse=True)
                            target_file = os.path.join(logs_dir, files[0])
                    else:
                        pot_file = os.path.join(logs_dir, f"{arg}.json")
                        if os.path.exists(pot_file): target_file = pot_file
                        
                    if target_file and os.path.exists(target_file):
                        with open(target_file, 'r') as f: data = json.load(f)
                        console.print(f"\n[bold cyan]🧠 Mission Result: {data.get('title', 'Unknown')} ({data.get('id')})[/bold cyan]")
                        console.print(f"[dim italic]Directive: {data.get('directive', '')}[/dim italic]\n")
                        report = data.get('report')
                        if report:
                            console.print(Panel(Markdown(report), title="[bold green]Final Report[/bold green]", border_style="green", padding=(1, 2)))
                        else:
                            console.print("[dim]No comprehensive report was generated for this mission.[/dim]")
                        console.print("\n")
                    else:
                        console.print(f"[bold red]Result {arg} not found.[/bold red]")
                continue
            if task.lower().startswith('/delete '):
                arg = task.lower().split()[1]
                import os
                logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
                if not os.path.exists(logs_dir):
                    console.print("[dim]No logs found.[/dim]")
                    continue
                target_file = None
                if arg == 'last':
                    files = [f for f in os.listdir(logs_dir) if f.endswith('.json')]
                    if files:
                        files.sort(key=lambda x: os.path.getmtime(os.path.join(logs_dir, x)), reverse=True)
                        target_file = os.path.join(logs_dir, files[0])
                else:
                    pot_file = os.path.join(logs_dir, f"{arg}.json")
                    if os.path.exists(pot_file): target_file = pot_file
                if target_file and os.path.exists(target_file):
                    os.remove(target_file)
                    console.print(f"[bold red]Log deleted.[/bold red]")
                else:
                    console.print(f"[dim]Log not found.[/dim]")
                continue
            if task.lower().startswith('/resume '):
                arg = task.lower().split()[1]
                import os, json
                logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
                target_file = None
                if arg == 'last':
                    files = [f for f in os.listdir(logs_dir) if f.endswith('.json')]
                    if files:
                        files.sort(key=lambda x: os.path.getmtime(os.path.join(logs_dir, x)), reverse=True)
                        target_file = os.path.join(logs_dir, files[0])
                else:
                    pot_file = os.path.join(logs_dir, f"{arg}.json")
                    if os.path.exists(pot_file): target_file = pot_file
                if target_file and os.path.exists(target_file):
                    with open(target_file, 'r') as f: data = json.load(f)
                    agent.history = []
                    global_tasks.clear()
                    from google.genai import types
                    agent.history.append(types.Content(role="user", parts=[types.Part.from_text(text=f"Please accomplish the following task: {data['directive']}")]))
                    for act in data.get('actions', []):
                        action_name = act.get('action')
                        args_dict = act.get('args', {})
                        agent.history.append(types.Content(role="model", parts=[types.Part.from_function_call(name=action_name, args=args_dict)]))
                        agent.history.append(types.Content(role="user", parts=[types.Part.from_function_response(name=action_name, response={"status": "success", "info": "Action replayed from log"})]))
                        if action_name == 'manage_tasks':
                            t_action = args_dict.get('action')
                            t_desc = args_dict.get('task_description')
                            if t_action == 'add': global_tasks.append({"desc": t_desc, "status": "pending"})
                            elif t_action == 'complete':
                                for t in global_tasks:
                                    if t['desc'] == t_desc: t['status'] = "completed"
                            elif t_action == 'clear': global_tasks.clear()
                    console.print(f"[bold green]Mission '{data.get('title')}' resumed. Memory and Tasks restored. Press Enter to continue.[/bold green]")
                else:
                    console.print("[dim]Log not found.[/dim]")
                continue
            if task.lower().startswith('/tasks '):
                tasks_str = task[7:].strip()
                tasks_list = [t.strip() for t in tasks_str.split(',') if t.strip()]
                for t in tasks_list:
                    global_tasks.append({"desc": t, "status": "pending"})
                console.print(f"[bold green]Injected {len(tasks_list)} tasks into the Task Manager.[/bold green]")
                continue
            if cmd == '/help':
                help_text = "**Available Slash Commands:**\n\n"
                for k, v in slash_commands.items():
                    help_text += f"- `{k}`: {v}\n"
                console.print(Panel(Markdown(help_text), border_style="blue"))
                continue
            if cmd == '/status':
                width, height = pyautogui.size()
                from core.config import KINESIS_VERSION
                status_text = f"**System Information:**\n- Primary Display Resolution: {width}x{height}\n- Fail-Safe: Active\n- API Model: gemini-3-flash-preview\n- Build Version: {KINESIS_VERSION}"
                console.print(Panel(Markdown(status_text), border_style="magenta"))
                continue
            if cmd == '/version':
                from core.config import KINESIS_VERSION
                console.print(f"[bold cyan]Kinesis Build Version:[/bold cyan] {KINESIS_VERSION}")
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
            dashboard.tasks = global_tasks
            step_counter = 1
            
            import time
            def get_renderable():
                dashboard.spinner.render(time.time()) # tick spinner
                return dashboard.build_layout()
                
            from core.logger import Logger
            logger = Logger(task) if logging_enabled else None
            
            # Start background autonomous task observer
            task_observer = TaskObserver(task, global_tasks, dashboard)
            task_observer.initialize_tasks_async()
            
            try:
                with Live(get_renderable(), console=console, refresh_per_second=15) as live:
                    for event in agent.run(task):
                        if event["type"] == "status" or event["type"] == "info":
                            dashboard.update_status(event['message'])
                            
                        elif event["type"] == "action":
                            thought = event.get('thought')
                            if thought:
                                dashboard.update_thought(thought)
                                if logger: logger.add_thought(thought)
                                
                            action_name = event['action_name']
                            args = event['args']
                            if logger: logger.add_action(action_name, args)
                            
                            if action_name == "mouse_action":
                                icon = "🖱️ "
                                action_desc = f"[bold green]{args.get('action').upper()}[/bold green]"
                                target = f"Model: ({args.get('x')}, {args.get('y')})"
                                if event.get('native_coords'):
                                    target += f" ➡️  [bold yellow]Native: {event['native_coords']}[/bold yellow]"
                            elif action_name == "keyboard_action":
                                icon = "⌨️ "
                                action_desc = f"[bold green]{args.get('action').upper()}[/bold green]"
                                target = f"Text: '{args.get('text', '')}' | Keys: {args.get('keys', [])}"
                            elif action_name == "shell_action":
                                icon = "🐚 "
                                action_desc = f"[bold green]EXECUTE SHELL[/bold green]"
                                target = f"[dim]{args.get('command', '')}[/dim]"
                            elif action_name == "scroll_action" or action_name == "scroll_document":
                                icon = "🖱️ "
                                action_desc = f"[bold green]SCROLL[/bold green]"
                                target = f"Clicks: {args.get('clicks', args.get('amount', 0))}"
                            elif action_name == "wait_action":
                                icon = "⏳ "
                                action_desc = f"[bold green]WAIT[/bold green]"
                                target = f"{args.get('seconds', 2)} seconds"
                            else:
                                icon = "⚙️ "
                                action_desc = f"[bold green]{action_name}[/bold green]"
                                target = str(args)
                                
                            dashboard.add_action(step_counter, icon, action_desc, target)
                            step_counter += 1
                            
                            # Notify TaskObserver of the progress
                            task_observer.update_tasks_async(thought or "", action_name, target)
                            
                        elif event["type"] == "ask_human":
                            question = event.get("question", "")
                            # Pause the live rendering briefly to ask the user
                            live.stop()
                            console.print(f"\n[bold yellow]🤖 KINESIS ASKS:[/bold yellow] {question}")
                            answer = session.prompt("Your response > ")
                            agent.bridge.human_response = answer
                            
                            # Add action to stream
                            dashboard.add_action(step_counter, "💬 ", "[bold yellow]ASK HUMAN[/bold yellow]", f"Q: {question} | A: {answer}")
                            step_counter += 1
                            
                            # Restart live rendering
                            live.start()
                            
                        elif event["type"] == "complete":
                            thought = event.get('thought')
                            if thought:
                                dashboard.update_thought(thought)
                            dashboard.update_status(f"✅ TASK COMPLETE: {event.get('status')}")
                            if logger: logger.report = event.get('report')
                            live.update(dashboard.build_layout())
                            time.sleep(1) # Let the user see completion before closing Live
                            console.print(Panel(f"✅ [bold green]TASK COMPLETE:[/bold green] {event.get('status')}", border_style="green", padding=(1, 2)))
                            if event.get('report'):
                                console.print("\n[bold cyan]Full Report Available! Type `/result last` to view it.[/bold cyan]")
                            
                        elif event["type"] == "error":
                            dashboard.update_status(f"❌ ERROR: {event['message']}")
                            live.update(dashboard.build_layout())
                            time.sleep(1)
                            console.print(Panel(f"❌ [bold red]ERROR:[/bold red] {event['message']}", border_style="red"))
                            
                        # Continually update the UI frame
                        live.update(get_renderable())
                        
            finally:
                if logger:
                    log_id, title = logger.save()
                    console.print(f"[bold green]Mission logged successfully as ID: {log_id}[/bold green] [dim]({title})[/dim]")
                
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
