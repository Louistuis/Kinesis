from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.spinner import Spinner
from rich.markdown import Markdown

class LiveDashboard:
    def __init__(self, task_directive: str):
        self.task_directive = task_directive
        self.actions = []
        self.current_thought = "Awaiting thought..."
        self.status_message = "Initializing..."
        self.spinner = Spinner("dots", style="bold green")
        self.tasks = []  # List of dicts: {"desc": "...", "status": "pending"|"completed"}
        
    def add_action(self, step_num: int, icon: str, desc: str, target: str):
        self.actions.append((str(step_num), icon, desc, target))
        if len(self.actions) > 10:
            self.actions.pop(0)
            
    def update_thought(self, thought: str):
        self.current_thought = thought
        
    def update_status(self, status: str):
        self.status_message = status
        
    def add_task(self, desc: str):
        self.tasks.append({"desc": desc, "status": "pending"})
        
    def complete_task(self, desc: str):
        for t in self.tasks:
            if t["desc"] == desc:
                t["status"] = "completed"
                break
                
    def clear_tasks(self):
        self.tasks = []

    def build_layout(self) -> Layout:
        layout = Layout()
        
        # Split into header, body, footer
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", minimum_size=15),
            Layout(name="footer", size=3)
        )
        
        # Split body into left (Action Stream) and right (Brain + Task Manager)
        layout["body"].split_row(
            Layout(name="action_log", ratio=2),
            Layout(name="right_panel", ratio=1)
        )
        
        # Split right panel into Brain and Task Manager
        layout["right_panel"].split_column(
            Layout(name="brain", ratio=2),
            Layout(name="tasks", ratio=1)
        )
        
        # Header
        header_text = Text(f" KINESIS DIRECTIVE: {self.task_directive} ", style="bold white on deep_sky_blue1", justify="center")
        layout["header"].update(Panel(header_text, style="deep_sky_blue1", border_style="deep_sky_blue1"))
        
        # Action Log Table
        table = Table(show_header=True, header_style="bold magenta", expand=True, border_style="magenta", box=None)
        table.add_column("Step", width=4, justify="center", no_wrap=True)
        table.add_column("Type", width=4, justify="center", no_wrap=True)
        table.add_column("Action", style="cyan", width=15, no_wrap=True, overflow="ellipsis")
        table.add_column("Target / Details", style="dim", no_wrap=True, overflow="ellipsis")
        
        for act in self.actions:
            table.add_row(act[0], act[1], act[2], act[3])
            
        layout["action_log"].update(Panel(table, title="[bold magenta]⚡ Action Stream[/bold magenta]", border_style="magenta", padding=(1, 2)))
        
        # Brain Panel
        brain_md = Markdown(self.current_thought)
        layout["brain"].update(Panel(brain_md, title="[bold blue]🧠 Internal Brain[/bold blue]", border_style="blue", padding=(1, 2)))
        
        # Task Manager Panel
        task_table = Table.grid(padding=(0, 1))
        task_table.add_column(style="bold", width=3)
        task_table.add_column(style="white", no_wrap=True, overflow="ellipsis")
        
        if not self.tasks:
            task_table.add_row("", "[dim italic]No active subtasks...[/dim italic]")
        else:
            for t in self.tasks:
                if t["status"] == "completed":
                    task_table.add_row("[green]✓[/green]", f"[dim strike]{t['desc']}[/dim strike]")
                else:
                    task_table.add_row("[yellow]○[/yellow]", t["desc"])
                    
        layout["tasks"].update(Panel(task_table, title="[bold green]📋 Task Manager[/bold green]", border_style="green", padding=(1, 2)))
        
        # Footer
        footer_content = Table.grid(expand=True)
        footer_content.add_column(width=3)
        footer_content.add_column(ratio=1)
        footer_content.add_row(
            self.spinner, Text(self.status_message, style="bold cyan")
        )
        layout["footer"].update(Panel(footer_content, border_style="cyan"))
        
        return layout
