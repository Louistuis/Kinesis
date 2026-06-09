import time
import pyautogui
from google.genai import types
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.live import Live
from rich.text import Text
from rich.table import Table
from rich.markdown import Markdown
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
import core.config

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
            'bottom-toolbar': 'bg:#1a1a2e #aaaaaa',
        })
        self.completer = WordCompleter(list(SLASH_COMMANDS.keys()), ignore_case=True)

    def bottom_toolbar(self):
        steps = self.state.total_steps
        cost = f"${self.state.estimated_cost:.3f}"
        elapsed = self.state.get_elapsed()
        return HTML(
            f' <b>KINESIS v{core.config.KINESIS_VERSION}</b>'
            f' │ Steps: {steps} │ Cost: {cost} │ ⏱ {elapsed}'
            f' │ <i>Ctrl+C to abort</i> │ <i>/help for commands</i> '
        )

    def start(self):
        while True:
            try:
                self.console.print()
                self.console.print(Rule(style="dim blue"))
                task = self.session.prompt(
                    "\n🚀 DIRECTIVE > ",
                    style=self.pt_style,
                    bottom_toolbar=self.bottom_toolbar,
                    completer=self.completer,
                )
                
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
                self.console.print("\n[bold red]⛔ FAIL-SAFE TRIGGERED — Mouse moved to screen corner. Execution aborted.[/bold red]")
            except KeyboardInterrupt:
                self.console.print("\n[bold yellow]⚠ Mission interrupted by user.[/bold yellow]")
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"\n[bold red]✗ Critical Error:[/bold red] {e}")

    def _run_agent_loop(self, task: str):
        # Reset per-mission state
        self.state.total_steps = 0
        self.state.api_calls = 0
        self.state.estimated_cost = 0.0
        self.state.consecutive_same_action = 0
        self.state.consecutive_popup_mentions = 0
        self.state.last_action_signature = ""
        mission_start = time.time()
        
        dashboard = LiveDashboard(task)
        dashboard.tasks = self.state.global_tasks
        step_counter = 1
        
        def get_renderable():
            dashboard.spinner.render(time.time())
            return dashboard.build_layout()
            
        logger = Logger(task) if self.state.logging_enabled else None
        
        task_observer = TaskObserver(task, self.state.global_tasks, dashboard)
        task_observer.initialize_tasks_async()
        
        # Pre-mission announcement
        self.console.print()
        self.console.print(Panel(
            Text.from_markup(
                f"[bold cyan]◉ Mission Accepted[/bold cyan]\n"
                f"[dim]Directive:[/dim] [white]{task}[/white]\n"
                f"[dim]Model:[/dim] [magenta]{core.config.MODEL_NAME}[/magenta] "
                f"[dim]│ Speed:[/dim] [yellow]{core.config.WAIT_TIME_SECONDS}s[/yellow] "
                f"[dim]│ Saving:[/dim] [green]{'On' if self.state.logging_enabled else 'Off'}[/green]"
            ),
            border_style="cyan",
            padding=(1, 2),
        ))
        self.console.print()
        
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
                        self.console.print()
                        self.console.print(Panel(
                            f"[bold yellow]🤖 KINESIS NEEDS YOUR INPUT[/bold yellow]\n\n{question}",
                            border_style="yellow",
                            padding=(1, 2),
                        ))
                        answer = self.session.prompt("  Your response > ")
                        self.agent.bridge.human_response = answer
                        dashboard.add_action(step_counter, "💬 ", "[bold yellow]ASK HUMAN[/bold yellow]", f"Q: {question} | A: {answer}")
                        step_counter += 1
                        live.start()
                        
                    elif event["type"] == "complete":
                        thought = event.get('thought')
                        if thought:
                            dashboard.update_thought(thought)
                        dashboard.update_status(f"✅ MISSION COMPLETE")
                        if logger: logger.report = event.get('report')
                        live.update(dashboard.build_layout())
                        time.sleep(1.5)
                        
                        # Premium completion summary
                        elapsed_secs = time.time() - mission_start
                        m, s = divmod(int(elapsed_secs), 60)
                        
                        summary = Table.grid(padding=(0, 2))
                        summary.add_column(style="bold cyan", justify="right")
                        summary.add_column(style="white")
                        summary.add_row("Status:", f"[bold green]{event.get('status', 'Completed')}[/bold green]")
                        summary.add_row("Duration:", f"{m}m {s:02d}s")
                        summary.add_row("Steps:", str(self.state.total_steps))
                        summary.add_row("API Calls:", str(self.state.api_calls))
                        summary.add_row("Est. Cost:", f"${self.state.estimated_cost:.4f}")
                        
                        self.console.print(Panel(
                            summary,
                            title="[bold green]✅ Mission Complete[/bold green]",
                            border_style="green",
                            padding=(1, 2),
                        ))
                        
                        if event.get('report'):
                            self.console.print(Panel(
                                Markdown(event['report']),
                                title="[bold cyan]📋 Final Report[/bold cyan]",
                                border_style="cyan",
                                padding=(1, 2),
                            ))
                        else:
                            self.console.print("[dim]Type /result last to view the full report.[/dim]")
                        
                    elif event["type"] == "error":
                        dashboard.update_status(f"❌ ERROR: {event['message']}")
                        live.update(dashboard.build_layout())
                        time.sleep(1)
                        self.console.print(Panel(
                            f"[bold red]✗ Error:[/bold red] {event['message']}",
                            border_style="red",
                            padding=(1, 2),
                        ))
                    
                    elif event["type"] == "metrics":
                        self.state.record_action(event["action_name"], event["args"], event.get("thought", ""))
                        
                        if self.state.consecutive_same_action >= 3:
                            dashboard.update_status("⚠️ Loop detected! Injecting alternative approach...")
                            self.agent.history.append(
                                types.Content(role="user", parts=[types.Part.from_text(
                                    text="SYSTEM OVERRIDE: You have repeated the same action 3+ times. You are STUCK IN A LOOP. "
                                         "You MUST try a completely different approach NOW. If you're trying to close a popup, "
                                         "try pressing Escape, or use keyboard shortcuts, or just ignore it and work around it."
                                )])
                            )
                            self.state.consecutive_same_action = 0
                        
                        if self.state.consecutive_popup_mentions >= 3:
                            dashboard.update_status("⚠️ Popup loop detected! Auto-pressing Escape...")
                            self.agent.bridge.execute_keyboard_action("press", keys=["escape"])
                            self.state.consecutive_popup_mentions = 0

                    elif event["type"] == "api_call":
                        self.state.record_api_call()

                    elif event["type"] == "check_pause":
                        while self.state.paused:
                            dashboard.update_status("⏸️ PAUSED — Type /pause to resume")
                            time.sleep(0.5)
                        
                    # Update dashboard vitals every event
                    w, h = pyautogui.size()
                    speed_name = "normal"
                    for name_key, val in core.config.SPEED_PRESETS.items():
                        if core.config.WAIT_TIME_SECONDS == val:
                            speed_name = name_key
                            break
                    dashboard.update_vitals(
                        steps=self.state.total_steps,
                        api_calls=self.state.api_calls,
                        cost=self.state.estimated_cost,
                        elapsed=self.state.get_elapsed_seconds(),
                        resolution=f"{w}x{h}",
                        speed=speed_name,
                    )
                        
                    live.update(get_renderable())
                    
        finally:
            if logger:
                log_id, title = logger.save()
                self.console.print()
                self.console.print(
                    f"  [bold green]◉ Mission saved[/bold green] "
                    f"[dim]ID:[/dim] [cyan]{log_id}[/cyan] "
                    f"[dim]Title:[/dim] [white]{title}[/white]"
                )

    def _format_action(self, event):
        action_name = event['action_name']
        args = event['args']
        if action_name == "mouse_action":
            icon = "🖱️ "
            action_desc = f"[bold green]{args.get('action', 'click').upper()}[/bold green]"
            target = f"({args.get('x')}, {args.get('y')})"
            if event.get('native_coords'):
                target += f" → [bold yellow]{event['native_coords']}[/bold yellow]"
        elif action_name in ("keyboard_action", "key_combination"):
            icon = "⌨️ "
            action_desc = f"[bold cyan]{args.get('action', 'press').upper()}[/bold cyan]"
            text_part = args.get('text', '')
            keys_part = args.get('keys', [])
            if text_part:
                target = f"'{text_part[:40]}'"
            elif keys_part:
                target = f"{keys_part}"
            else:
                target = str(args)[:50]
        elif action_name == "shell_action":
            icon = "🐚 "
            action_desc = f"[bold yellow]SHELL[/bold yellow]"
            target = f"{args.get('command', '')[:60]}"
        elif action_name in ("scroll_action", "scroll_document"):
            icon = "📜 "
            action_desc = f"[bold blue]SCROLL[/bold blue]"
            target = f"{args.get('direction', '')} {args.get('clicks', args.get('amount', ''))}"
        elif action_name in ("wait_action", "wait", "wait_5_seconds"):
            icon = "⏳ "
            action_desc = f"[dim]WAIT[/dim]"
            target = f"{args.get('seconds', 2)}s"
        elif action_name == "computer_use":
            icon = "🖥️ "
            action = args.get('action', '')
            action_desc = f"[bold magenta]{action.upper()}[/bold magenta]"
            coords = args.get('coordinates', [])
            target = f"{coords}" if coords else str(args.get('text', ''))[:40]
        elif action_name == "task_complete":
            icon = "✅ "
            action_desc = f"[bold green]COMPLETE[/bold green]"
            target = args.get('status', '')
        elif action_name == "ask_human":
            icon = "💬 "
            action_desc = f"[bold yellow]ASK HUMAN[/bold yellow]"
            target = args.get('question', '')[:50]
        else:
            icon = "⚙️ "
            action_desc = f"[bold]{action_name}[/bold]"
            target = str(args)[:50]
        return icon, action_desc, target
