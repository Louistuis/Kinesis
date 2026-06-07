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
        self.spinner = Spinner("bouncingBar", style="bold cyan")
        
    def add_action(self, step_num: int, icon: str, desc: str, target: str):
        self.actions.append((str(step_num), icon, desc, target))
        # Keep only the last 10 actions to prevent the table from growing too tall in-line
        if len(self.actions) > 8:
            self.actions.pop(0)
            
    def update_thought(self, thought: str):
        self.current_thought = thought
        
    def update_status(self, status: str):
        self.status_message = status

    def build_layout(self) -> Layout:
        layout = Layout()
        
        # Split into header, body, footer
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", minimum_size=12),
            Layout(name="footer", size=3)
        )
        
        # Split body into left and right
        layout["body"].split_row(
            Layout(name="action_log", ratio=2),
            Layout(name="brain", ratio=1)
        )
        
        # Header
        header_text = Text(f"🚀 DIRECTIVE: {self.task_directive}", style="bold white on deep_sky_blue1", justify="center")
        layout["header"].update(Panel(header_text, style="deep_sky_blue1"))
        
        # Action Log Table
        table = Table(show_header=True, header_style="bold magenta", expand=True, border_style="dim")
        table.add_column("Step", width=4, justify="center")
        table.add_column("Type", width=4, justify="center")
        table.add_column("Action", style="cyan", width=15)
        table.add_column("Target / Details", style="dim")
        
        for act in self.actions:
            table.add_row(act[0], act[1], act[2], act[3])
            
        layout["action_log"].update(Panel(table, title="[bold magenta]Action Stream[/bold magenta]", border_style="magenta"))
        
        # Brain Panel
        brain_md = Markdown(self.current_thought)
        layout["brain"].update(Panel(brain_md, title="[bold blue]🧠 Internal Brain[/bold blue]", border_style="blue"))
        
        # Footer
        footer_content = Table.grid(expand=True)
        footer_content.add_column(ratio=1)
        footer_content.add_row(
            Text.assemble(self.spinner.render(0), " ", Text(self.status_message, style="bold cyan"))
        )
        layout["footer"].update(Panel(footer_content, border_style="cyan"))
        
        return layout
