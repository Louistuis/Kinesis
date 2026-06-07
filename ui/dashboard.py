from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.spinner import Spinner
from rich.markdown import Markdown

THEMES = {
    1: {"primary": "magenta", "secondary": "cyan", "border": "blue", "success": "green", "warning": "yellow", "danger": "red", "dim": "dim", "text": "white", "header_bg": "deep_sky_blue1"},
    2: {"primary": "bright_blue", "secondary": "bright_white", "border": "white", "success": "bright_green", "warning": "bright_yellow", "danger": "bright_red", "dim": "dim white", "text": "white", "header_bg": "bright_black"},
    3: {"primary": "green", "secondary": "green", "border": "green", "success": "bright_green", "warning": "green", "danger": "bright_green", "dim": "dim green", "text": "bright_green", "header_bg": "black"}
}

class LiveDashboard:
    def __init__(self, task_directive: str, theme_id: int = 1):
        self.task_directive = task_directive
        self.theme = THEMES.get(theme_id, THEMES[1])
        self.actions = []
        self.current_thought = "Awaiting thought..."
        self.status_message = "Initializing..."
        self.spinner = Spinner("dots", style=f"bold {self.theme['success']}")
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
        t = self.theme
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
        header_text = Text(f" KINESIS DIRECTIVE: {self.task_directive} ", style=f"bold {t['text']} on {t['header_bg']}", justify="center")
        layout["header"].update(Panel(header_text, style=t['header_bg'], border_style=t['header_bg']))
        
        # Action Log Table
        table = Table(show_header=True, header_style=f"bold {t['primary']}", expand=True, border_style=t['primary'], box=None)
        table.add_column("Step", width=4, justify="center", no_wrap=True)
        table.add_column("Type", width=4, justify="center", no_wrap=True)
        table.add_column("Action", style=t['secondary'], width=15, no_wrap=True, overflow="ellipsis")
        table.add_column("Target / Details", style=t['dim'], no_wrap=True, overflow="ellipsis")
        
        for act in self.actions:
            table.add_row(act[0], act[1], act[2], act[3])
            
        layout["action_log"].update(Panel(table, title=f"[bold {t['primary']}]⚡ Action Stream[/bold {t['primary']}]", border_style=t['primary'], padding=(1, 2)))
        
        # Brain Panel
        brain_md = Markdown(self.current_thought)
        layout["brain"].update(Panel(brain_md, title=f"[bold {t['border']}]🧠 Internal Brain[/bold {t['border']}]", border_style=t['border'], padding=(1, 2)))
        
        # Task Manager Panel
        task_table = Table.grid(padding=(0, 1))
        task_table.add_column(style="bold", width=3)
        task_table.add_column(style=t['text'], no_wrap=True, overflow="ellipsis")
        
        if not self.tasks:
            task_table.add_row("", f"[{t['dim']} italic]No active subtasks...[/{t['dim']} italic]")
        else:
            for task in self.tasks:
                if task["status"] == "completed":
                    task_table.add_row(f"[{t['success']}]✓[/{t['success']}]", f"[{t['dim']} strike]{task['desc']}[/{t['dim']} strike]")
                else:
                    task_table.add_row(f"[{t['warning']}]○[/{t['warning']}]", task["desc"])
                    
        layout["tasks"].update(Panel(task_table, title=f"[bold {t['success']}]📋 Task Manager[/bold {t['success']}]", border_style=t['success'], padding=(1, 2)))
        
        # Footer
        footer_content = Table.grid(expand=True)
        footer_content.add_column(width=3)
        footer_content.add_column(ratio=1)
        footer_content.add_row(
            self.spinner, Text(self.status_message, style=f"bold {t['secondary']}")
        )
        layout["footer"].update(Panel(footer_content, border_style=t['secondary']))
        
        return layout
