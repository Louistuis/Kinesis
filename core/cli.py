import time
import pyautogui
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.live import Live
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.completion import WordCompleter

from core.state import CLIState
from core.commands import CommandProcessor, SLASH_COMMANDS
from core.agent import MacAgent
from core.task_observer import TaskObserver
from core.logger import Logger
from ui.dashboard import LiveDashboard

class KinesisCLI:
    def __init__(self, console: Console, agent: MacAgent, cursor_process):
        self.console = console
        self.agent = agent
        self.cursor_process = cursor_process
        self.state = CLIState()
        self.cmd_processor = CommandProcessor(self.console, self.state, self.agent, self.cursor_process)
        
        self.session = PromptSession(history=InMemoryHistory())
        self.pt_style = Style.from_dict({
            'prompt': 'ansicyan bold',
            'bottom-toolbar': 'bg:#222222 #aaaaaa',
        })
        self.completer = WordCompleter(list(SLASH_COMMANDS.keys()), ignore_case=True)

    def bottom_toolbar(self):
        return HTML(' <b>Kinesis CLI</b> • Autonomous Agent • Press Ctrl+C to abort task • Type /help for commands ')

    def start(self):
        while True:
            try:
                self.console.print("\n", Rule(style="cyan"))
                task = self.session.prompt("\n🚀 DIRECTIVE > ", style=self.pt_style, bottom_toolbar=self.bottom_toolbar, completer=self.completer)
                
                if not task.strip():
                    continue
                    
                # Process slash commands
                cmd_result = self.cmd_processor.process(task)
                if cmd_result == "EXIT":
                    break
                elif cmd_result is True:
                    continue
                
                # Run Agent
                self._run_agent_loop(task)
                
            except pyautogui.FailSafeException:
                self.console.print("\n[bold red][FAIL-SAFE TRIGGERED] Mouse moved to screen corner. Execution aggressively aborted.[/bold red]")
            except KeyboardInterrupt:
                self.console.print("\n[warning]Task interrupted.[/warning]")
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"\n[danger]Critical Error:[/danger] {e}")

    def _run_agent_loop(self, task: str):
        dashboard = LiveDashboard(task)
        dashboard.tasks = self.state.global_tasks
        step_counter = 1
        
        def get_renderable():
            dashboard.spinner.render(time.time())
            return dashboard.build_layout()
            
        logger = Logger(task) if self.state.logging_enabled else None
        
        task_observer = TaskObserver(task, self.state.global_tasks, dashboard)
        task_observer.initialize_tasks_async()
        
        try:
            with Live(get_renderable(), console=self.console, refresh_per_second=15) as live:
                for event in self.agent.run(task, self.state.global_tasks):
                    if event["type"] == "status" or event["type"] == "info":
                        dashboard.update_status(event['message'])
                        
                    elif event["type"] == "action":
                        thought = event.get('thought')
                        if thought:
                            dashboard.update_thought(thought)
                            if logger: logger.add_thought(thought)
                            if self.state.voice_enabled:
                                import subprocess
                                first_sentence = thought.split('.')[0].strip()
                                if first_sentence:
                                    subprocess.Popen(['say', first_sentence])
                            
                        action_name = event['action_name']
                        args = event['args']
                        if logger: logger.add_action(action_name, args)
                        
                        icon, action_desc, target = self._format_action(event)
                        dashboard.add_action(step_counter, icon, action_desc, target)
                        step_counter += 1
                        
                        task_observer.update_tasks_async(thought or "", action_name, target)
                        
                    elif event["type"] == "ask_human":
                        question = event.get("question", "")
                        live.stop()
                        self.console.print(f"\n[bold yellow]🤖 KINESIS ASKS:[/bold yellow] {question}")
                        answer = self.session.prompt("Your response > ")
                        self.agent.bridge.human_response = answer
                        dashboard.add_action(step_counter, "💬 ", "[bold yellow]ASK HUMAN[/bold yellow]", f"Q: {question} | A: {answer}")
                        step_counter += 1
                        live.start()
                        
                    elif event["type"] == "complete":
                        thought = event.get('thought')
                        if thought:
                            dashboard.update_thought(thought)
                        dashboard.update_status(f"✅ TASK COMPLETE: {event.get('status')}")
                        if logger: logger.report = event.get('report')
                        live.update(dashboard.build_layout())
                        time.sleep(1)
                        self.console.print(Panel(f"✅ [bold green]TASK COMPLETE:[/bold green] {event.get('status')}", border_style="green", padding=(1, 2)))
                        if event.get('report'):
                            self.console.print("\n[bold cyan]Full Report Available! Type `/result last` to view it.[/bold cyan]")
                        
                    elif event["type"] == "error":
                        dashboard.update_status(f"❌ ERROR: {event['message']}")
                        live.update(dashboard.build_layout())
                        time.sleep(1)
                        self.console.print(Panel(f"❌ [bold red]ERROR:[/bold red] {event['message']}", border_style="red"))
                        
                    live.update(get_renderable())
                    
        finally:
            if logger:
                log_id, title = logger.save()
                self.console.print(f"[bold green]Mission logged successfully as ID: {log_id}[/bold green] [dim]({title})[/dim]")

    def _format_action(self, event):
        action_name = event['action_name']
        args = event['args']
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
        return icon, action_desc, target
