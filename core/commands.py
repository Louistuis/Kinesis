import os
import sys
import json
import subprocess
import pyautogui
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from core.state import CLIState

# Replicate slash_commands dict
SLASH_COMMANDS = {
    "/help": "Show available commands",
    "/info": "Show help and information regarding Kinesis setup and features",
    "/exit": "Exit Kinesis CLI",
    "/quit": "Exit Kinesis CLI",
    "/clear": "Clear the terminal screen and agent memory",
    "/setup": "Restart the setup wizard to change API keys",
    "/status": "Show agent status and system info",
    "/version": "Show current Kinesis build version",
    "/update": "Pull latest code and instantly hot-reload Kinesis",
    "/tasks": "Inject tasks into the Task Manager (e.g., /tasks 'Find email', 'Reply')",
    "/list": "List all saved mission logs and results",
    "/save on": "Enable mission saving and AI auto-naming",
    "/save off": "Disable mission saving",
    "/result <id>": "View the comprehensive final report of a mission",
    "/result log <id>": "View the chronological actions taken in a mission",
    "/delete <id>": "Delete a mission log by ID or 'last'",
    "/resume <id>": "Resume a mission log by ID or 'last'",
    "/debug <id>": "View an advanced execution trace and latency for a mission",
    "/voice on": "Enable Kinesis voice (speaks out loud its thoughts)",
    "/voice off": "Disable Kinesis voice",
}

class CommandProcessor:
    def __init__(self, console: Console, state: CLIState, agent, cursor_process):
        self.console = console
        self.state = state
        self.agent = agent
        self.cursor_process = cursor_process

    def process(self, task: str) -> bool:
        """
        Processes a potential slash command.
        Returns True if a command was processed (meaning the REPL should continue to the next prompt).
        Returns False if the input is a regular task and should be passed to the agent.
        If it returns "EXIT", the program should exit.
        """
        cmd = task.lower().strip()
        
        if cmd in ['/exit', '/quit', 'exit', 'quit']:
            self.console.print("[dim]Exiting Kinesis CLI... Goodbye.[/dim]")
            return "EXIT"
            
        if cmd == '/setup':
            setup_marker = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".setup_complete")
            if os.path.exists(setup_marker):
                os.remove(setup_marker)
            self.console.print("\n[dim]Restarting Kinesis for Setup Wizard...[/dim]")
            try: self.cursor_process.terminate()
            except: pass
            os.execv(sys.executable, [sys.executable, "main.py"])
            
        if cmd == '/clear':
            os.system('clear')
            self.console.clear()
            self.agent.history = []
            self.state.clear_tasks()
            self.console.print("[dim]Terminal, agent memory, and task manager cleared.[/dim]")
            return True
            
        if task.lower().startswith('/save'):
            args = task.lower().split()
            if len(args) == 2 and args[1] == 'on':
                self.state.logging_enabled = True
                self.console.print("[bold green]Mission saving enabled.[/bold green]")
            elif len(args) == 2 and args[1] == 'off':
                self.state.logging_enabled = False
                self.console.print("[dim]Mission saving disabled.[/dim]")
            else:
                self.console.print("[dim]Usage: /save on | /save off[/dim]")
            return True
            
        if task.lower().startswith('/voice'):
            args = task.lower().split()
            if len(args) == 2 and args[1] == 'on':
                self.state.voice_enabled = True
                self.console.print("[bold green]Voice enabled. Kinesis will speak its thoughts.[/bold green]")
            elif len(args) == 2 and args[1] == 'off':
                self.state.voice_enabled = False
                self.console.print("[dim]Voice disabled.[/dim]")
            else:
                self.console.print("[dim]Usage: /voice on | /voice off[/dim]")
            return True
            
        if cmd == '/list':
            logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
            if not os.path.exists(logs_dir) or not os.listdir(logs_dir):
                self.console.print("[dim]No missions found.[/dim]")
                return True
            table = Table(title="Mission History", show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="green")
            table.add_column("Timestamp", style="dim")
            logs = []
            for f in os.listdir(logs_dir):
                if f.endswith('.json'):
                    with open(os.path.join(logs_dir, f), 'r') as log_file:
                        try: logs.append(json.load(log_file))
                        except: pass
            logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            for log in logs:
                table.add_row(log.get('id', ''), log.get('title', ''), log.get('timestamp', '')[:16].replace('T', ' '))
            self.console.print(table)
            return True
            
        if task.lower().startswith('/result '):
            args = task.lower().split()
            if len(args) == 2 or (len(args) == 3 and args[1] == 'log'):
                arg = args[1] if len(args) == 2 else args[2]
                logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
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
                    
                    if len(args) == 3 and args[1] == 'log':
                        self.console.print(f"\n[bold cyan]🧠 Mission Actions: {data.get('title', 'Unknown')} ({data.get('id')})[/bold cyan]")
                        self.console.print(f"[dim italic]Directive: {data.get('directive', '')}[/dim italic]\n")
                        for i, act in enumerate(data.get('actions', [])):
                            self.console.print(f"  [bold magenta]{i+1}.[/bold magenta] {act.get('action').upper()}: {act.get('args')}")
                        self.console.print("\n")
                    else:
                        self.console.print(f"\n[bold cyan]🧠 Mission Result: {data.get('title', 'Unknown')} ({data.get('id')})[/bold cyan]")
                        self.console.print(f"[dim italic]Directive: {data.get('directive', '')}[/dim italic]\n")
                        report = data.get('report')
                        if report:
                            self.console.print(Panel(Markdown(report), title="[bold green]Final Report[/bold green]", border_style="green", padding=(1, 2)))
                        else:
                            self.console.print("[dim]No comprehensive report was generated for this mission.[/dim]")
                        self.console.print("\n")
                else:
                    self.console.print(f"[bold red]Result {arg} not found.[/bold red]")
            else:
                self.console.print("[dim]Usage: /result <id> | /result log <id>[/dim]")
            return True
            
        if task.lower().startswith('/delete '):
            arg = task.lower().split()[1]
            logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
            if not os.path.exists(logs_dir):
                self.console.print("[dim]No logs found.[/dim]")
                return True
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
                self.console.print(f"[bold red]Log deleted.[/bold red]")
            else:
                self.console.print(f"[dim]Log not found.[/dim]")
            return True
            
        if task.lower().startswith('/debug '):
            arg = task.lower().split()[1]
            logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
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
                
                self.console.print(f"\n[bold yellow]🛠️ ADVANCED DEBUG TRACE: {data.get('title', 'Unknown')} ({data.get('id')})[/bold yellow]")
                
                # Weave thoughts and actions
                thoughts = data.get('thoughts', [])
                actions = data.get('actions', [])
                
                # Combine and sort by timestamp
                trace = []
                for t in thoughts:
                    trace.append({"type": "THOUGHT", "time": t.get("timestamp"), "content": t.get("thought")})
                for a in actions:
                    trace.append({"type": "ACTION", "time": a.get("timestamp"), "content": f"{a.get('action').upper()} -> {a.get('args')}"})
                    
                trace.sort(key=lambda x: x["time"])
                
                from datetime import datetime
                
                table = Table(title="Execution Trace", show_header=True, header_style="bold yellow")
                table.add_column("Step", style="dim", justify="right")
                table.add_column("Type", style="magenta")
                table.add_column("Latency", style="cyan")
                table.add_column("Content", style="green", overflow="fold")
                
                last_time = None
                for i, step in enumerate(trace):
                    try:
                        curr_time = datetime.fromisoformat(step["time"])
                        latency = f"{(curr_time - last_time).total_seconds():.2f}s" if last_time else "0.00s"
                        last_time = curr_time
                    except:
                        latency = "N/A"
                        
                    table.add_row(str(i+1), step["type"], latency, str(step["content"]))
                    
                self.console.print(table)
            else:
                self.console.print(f"[bold red]Log not found for debug trace.[/bold red]")
            return True
            
        if task.lower().startswith('/resume '):
            arg = task.lower().split()[1]
            logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
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
                self.agent.history = []
                self.state.clear_tasks()
                from google.genai import types
                self.agent.history.append(types.Content(role="user", parts=[types.Part.from_text(text=f"Please accomplish the following task: {data['directive']}")]))
                for act in data.get('actions', []):
                    action_name = act.get('action')
                    args_dict = act.get('args', {})
                    self.agent.history.append(types.Content(role="model", parts=[types.Part.from_function_call(name=action_name, args=args_dict)]))
                    self.agent.history.append(types.Content(role="user", parts=[types.Part.from_function_response(name=action_name, response={"status": "success", "info": "Action replayed from log"})]))
                    if action_name == 'manage_tasks':
                        t_action = args_dict.get('action')
                        t_desc = args_dict.get('task_description')
                        if t_action == 'add': self.state.add_task(t_desc)
                        elif t_action == 'complete':
                            for t in self.state.global_tasks:
                                if t['desc'] == t_desc: t['status'] = "completed"
                        elif t_action == 'clear': self.state.clear_tasks()
                self.console.print(f"[bold green]Mission '{data.get('title')}' resumed. Memory and Tasks restored. Press Enter to continue.[/bold green]")
            else:
                self.console.print("[dim]Log not found.[/dim]")
            return True
            
        if task.lower().startswith('/tasks '):
            tasks_str = task[7:].strip()
            tasks_list = [t.strip() for t in tasks_str.split(',') if t.strip()]
            for t in tasks_list:
                self.state.add_task(t)
            self.console.print(f"[bold green]Injected {len(tasks_list)} tasks into the Task Manager.[/bold green]")
            return True
            
        if cmd == '/help':
            help_text = "**Available Slash Commands:**\n\n"
            for k, v in SLASH_COMMANDS.items():
                help_text += f"- `{k}`: {v}\n"
            self.console.print(Panel(Markdown(help_text), border_style="blue"))
            return True
            
        if cmd == '/status':
            width, height = pyautogui.size()
            from core.config import KINESIS_VERSION
            log_status = "Enabled" if self.state.logging_enabled else "Disabled"
            voice_status = "Enabled" if self.state.voice_enabled else "Disabled"
            status_text = f"**System Information:**\n- Primary Display Resolution: {width}x{height}\n- Fail-Safe: Active\n- API Model: gemini-3-flash-preview\n- Build Version: {KINESIS_VERSION}\n- Logging: {log_status}\n- Voice TTS: {voice_status}"
            self.console.print(Panel(Markdown(status_text), border_style="magenta"))
            return True
            
        if cmd == '/info':
            info_text = """
# Welcome to Kinesis Info 📘

**Authentication**
Kinesis supports two authentication modes, configurable via `/setup`:
1. **API Key**: A raw Gemini API Key.
2. **OAuth / Application Default Credentials**: Uses your local `gcloud` or `gemini cli` credentials. You can set this up interactively by running `/setup` and choosing Option 3 to securely authenticate via your browser!

**Features**
- **Autonomous Control**: Give Kinesis a directive (e.g. `play some chess`), and it will break it down into tasks and execute it entirely on its own.
- **Chain of Thought (CoT)**: Kinesis natively explains its reasoning step-by-step in the Internal Brain card.
- **Voice Mode**: Use `/voice on` to have Kinesis audibly speak its thought process as it works!
- **Mission Logs**: Use `/save on` to record your missions. View them later with `/list`, `/result <id>`, and `/result log <id>`.
- **Hot-Reload Updates**: Use `/update` to pull the latest codebase from GitHub and instantly restart Kinesis without closing your terminal.

**Safety**
- **Fail-Safe**: If Kinesis is running amok, physically move your mouse cursor to any corner of your screen (e.g. top-left) to instantly trigger the PyAutoGUI fail-safe and abort execution!
"""
            self.console.print(Panel(Markdown(info_text), border_style="cyan", title="[bold white]Kinesis Overview[/bold white]"))
            return True
            
        if cmd == '/version':
            from core.config import KINESIS_VERSION
            self.console.print(f"[bold cyan]Kinesis Build Version:[/bold cyan] {KINESIS_VERSION}")
            return True
            
        if cmd == '/update':
            self.console.print("\n[dim]Pulling latest changes from GitHub...[/dim]")
            subprocess.run(["git", "pull", "origin", "master"])
            self.console.print("[bold green]Update complete. Hot-reloading Kinesis...[/bold green]")
            try: self.cursor_process.terminate()
            except: pass
            os.execv(sys.executable, [sys.executable, "main.py"])
            
        if cmd.startswith('/'):
            self.console.print(f"[dim]Unknown command: {cmd}[/dim]")
            return True
            
        return False
