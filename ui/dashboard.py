import time
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.spinner import Spinner
from rich.markdown import Markdown
from rich.align import Align
from rich.console import Group


class LiveDashboard:
    """Cyberpunk-themed 5-panel TUI dashboard for the Kinesis agent."""

    def __init__(self, task_directive: str):
        self.task_directive = task_directive
        self.start_time = time.time()

        # Cyberpunk theme palette
        self.theme = {
            "primary": "magenta",
            "secondary": "cyan",
            "border": "blue",
            "success": "green",
            "warning": "yellow",
            "danger": "red",
            "dim": "dim",
            "text": "white",
            "header_bg": "deep_sky_blue1",
            "accent": "bright_magenta",
            "vitals": "dark_orange",
        }

        self.actions: list[tuple[str, str, str, str, float]] = []
        self.current_thought: str = ""
        self.status_message: str = "Initializing..."
        self.spinner = Spinner("dots", style=f"bold {self.theme['success']}")
        self.tasks: list[dict[str, str]] = []

        # Vitals data
        self._vitals_steps: int = 0
        self._vitals_api_calls: int = 0
        self._vitals_cost: float = 0.0
        self._vitals_elapsed: float = 0.0
        self._vitals_resolution: str = "—"
        self._vitals_speed: str = "normal"

    # ── Public interface ────────────────────────────────────────

    def add_action(self, step_num: int, icon: str, desc: str, target: str) -> None:
        """Append an action row with an automatic timestamp."""
        self.actions.append((str(step_num), icon, desc, target, time.time()))
        if len(self.actions) > 12:
            self.actions.pop(0)

    def update_thought(self, thought: str) -> None:
        self.current_thought = thought

    def update_status(self, status: str) -> None:
        self.status_message = status

    def add_task(self, desc: str) -> None:
        self.tasks.append({"desc": desc, "status": "pending"})

    def complete_task(self, desc: str) -> None:
        for t in self.tasks:
            if t["desc"] == desc:
                t["status"] = "completed"
                break

    def clear_tasks(self) -> None:
        self.tasks = []

    def update_vitals(
        self,
        steps: int,
        api_calls: int,
        cost: float,
        elapsed: float,
        resolution: str,
        speed: str,
    ) -> None:
        """Update system vitals for the bottom-right panel."""
        self._vitals_steps = steps
        self._vitals_api_calls = api_calls
        self._vitals_cost = cost
        self._vitals_elapsed = elapsed
        self._vitals_resolution = resolution
        self._vitals_speed = speed

    # ── Layout builder ──────────────────────────────────────────

    def build_layout(self) -> Layout:
        t = self.theme
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body", minimum_size=15),
            Layout(name="footer", size=3),
        )

        # Body: left (action stream) | right (brain / tasks / vitals)
        layout["body"].split_row(
            Layout(name="action_log", ratio=2),
            Layout(name="right_col", ratio=2),
        )

        layout["right_col"].split_column(
            Layout(name="brain", ratio=2),
            Layout(name="tasks", ratio=1),
            Layout(name="vitals", ratio=1),
        )

        # ── Header ──────────────────────────────────────────────
        layout["header"].update(self._build_header(t))

        # ── Action Stream ───────────────────────────────────────
        layout["action_log"].update(self._build_action_stream(t))

        # ── Internal Brain ──────────────────────────────────────
        layout["brain"].update(self._build_brain(t))

        # ── Task Manager ────────────────────────────────────────
        layout["tasks"].update(self._build_task_manager(t))

        # ── System Vitals ───────────────────────────────────────
        layout["vitals"].update(self._build_vitals(t))

        # ── Footer ──────────────────────────────────────────────
        layout["footer"].update(self._build_footer(t))

        return layout

    # ── Private panel builders ──────────────────────────────────

    def _fmt_elapsed(self, seconds: float) -> str:
        """Format seconds into 0m 00s."""
        m, s = divmod(int(seconds), 60)
        return f"{m}m {s:02d}s"

    def _build_header(self, t: dict) -> Panel:
        grid = Table.grid(expand=True, padding=0)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="center", ratio=2)
        grid.add_column(justify="right", ratio=1)

        left = Text.from_markup(
            f"[bold {t['accent']}]◉ KINESIS[/bold {t['accent']}]"
            f" [bold {t['dim']}]v1.0.0[/bold {t['dim']}]"
        )

        directive = self.task_directive
        if len(directive) > 60:
            directive = directive[:57] + "..."
        center = Text.from_markup(
            f"[bold {t['secondary']}]Mission:[/bold {t['secondary']}] "
            f"[{t['text']}]{directive}[/{t['text']}]"
        )

        elapsed = time.time() - self.start_time
        right = Text.from_markup(
            f"[{t['warning']}]⏱ {self._fmt_elapsed(elapsed)}[/{t['warning']}]"
            f" [{t['dim']}]│[/{t['dim']}] "
            f"[bold {t['secondary']}]#{self._vitals_steps}[/bold {t['secondary']}]"
        )

        grid.add_row(left, center, right)
        return Panel(
            grid,
            style=f"on {t['header_bg']}",
            border_style=t["header_bg"],
        )

    def _action_style(self, icon: str, t: dict) -> str:
        """Pick a row style based on the action icon / type."""
        icon_lower = icon.lower()
        mapping = {
            "🖱": t["success"],
            "mouse": t["success"],
            "⌨": t["secondary"],
            "key": t["secondary"],
            "type": t["secondary"],
            "🐚": t["warning"],
            "shell": t["warning"],
            "$": t["warning"],
            "📜": t["border"],
            "scroll": t["border"],
            "⏳": t["dim"],
            "wait": t["dim"],
        }
        for key, style in mapping.items():
            if key in icon_lower:
                return style
        return t["text"]

    def _build_action_stream(self, t: dict) -> Panel:
        table = Table(
            show_header=True,
            header_style=f"bold {t['primary']}",
            expand=True,
            border_style=t["primary"],
            box=None,
            pad_edge=False,
        )
        table.add_column("Step", width=5, justify="center", no_wrap=True)
        table.add_column("Time", width=7, justify="right", no_wrap=True, style=t["dim"])
        table.add_column("", width=3, justify="center", no_wrap=True)
        table.add_column("Action", min_width=14, no_wrap=True, overflow="ellipsis")
        table.add_column("Target / Details", ratio=1, no_wrap=True, overflow="ellipsis", style=t["dim"])

        for step, icon, desc, target, ts in self.actions:
            rel = ts - self.start_time
            time_str = f"+{rel:.1f}s"
            row_style = self._action_style(icon, t)
            table.add_row(
                f"[{row_style}]{step}[/{row_style}]",
                f"[{t['dim']}]{time_str}[/{t['dim']}]",
                icon,
                f"[{row_style}]{desc}[/{row_style}]",
                f"[{t['dim']}]{target}[/{t['dim']}]",
            )

        return Panel(
            table,
            title=f"[bold {t['primary']}]⚡ Action Stream[/bold {t['primary']}]",
            border_style=t["primary"],
            padding=(1, 2),
        )

    def _build_brain(self, t: dict) -> Panel:
        if self.current_thought:
            content = Markdown(self.current_thought)
        else:
            content = Text(
                "Awaiting thought…",
                style=f"italic {t['dim']}",
                justify="center",
            )

        return Panel(
            content,
            title=f"[bold {t['border']}]🧠 Internal Brain[/bold {t['border']}]",
            border_style=t["border"],
            padding=(1, 2),
        )

    def _build_task_manager(self, t: dict) -> Panel:
        task_grid = Table.grid(padding=(0, 1), expand=True)
        task_grid.add_column(style="bold", width=3)
        task_grid.add_column(style=t["text"], no_wrap=True, overflow="ellipsis", ratio=1)

        if not self.tasks:
            task_grid.add_row(
                "",
                f"[{t['dim']} italic]No active subtasks…[/{t['dim']} italic]",
            )
        else:
            first_pending = True
            for task in self.tasks:
                if task["status"] == "completed":
                    task_grid.add_row(
                        f"[{t['success']}]✓[/{t['success']}]",
                        f"[{t['dim']} strike]{task['desc']}[/{t['dim']} strike]",
                    )
                else:
                    if first_pending:
                        task_grid.add_row(
                            self.spinner,
                            f"[bold {t['warning']}]{task['desc']}[/bold {t['warning']}]",
                        )
                        first_pending = False
                    else:
                        task_grid.add_row(
                            f"[{t['dim']}]○[/{t['dim']}]",
                            f"[{t['dim']}]{task['desc']}[/{t['dim']}]",
                        )

        # Progress bar
        total = len(self.tasks)
        done = sum(1 for tk in self.tasks if tk["status"] == "completed")
        pct = (done / total * 100) if total else 0
        bar_width = 16
        filled = int(bar_width * done / total) if total else 0
        empty = bar_width - filled
        bar = f"[{t['success']}]{'█' * filled}[/{t['success']}][{t['dim']}]{'░' * empty}[/{t['dim']}]"
        progress_line = Text.from_markup(
            f"\n[bold {t['secondary']}]Progress:[/bold {t['secondary']}] {bar}"
            f" [{t['text']}]{done}/{total}[/{t['text']}]"
            f" [{t['dim']}]({pct:.0f}%)[/{t['dim']}]"
        )

        content = Group(task_grid, progress_line)

        return Panel(
            content,
            title=f"[bold {t['success']}]📋 Task Manager[/bold {t['success']}]",
            border_style=t["success"],
            padding=(1, 2),
        )

    def _build_vitals(self, t: dict) -> Panel:
        grid = Table.grid(padding=(0, 2), expand=True)
        grid.add_column(style=f"bold {t['vitals']}", justify="right", no_wrap=True)
        grid.add_column(style=t["text"], no_wrap=True)
        grid.add_column(style=f"bold {t['vitals']}", justify="right", no_wrap=True)
        grid.add_column(style=t["text"], no_wrap=True)

        grid.add_row(
            "Steps:",
            f"[bold {t['secondary']}]{self._vitals_steps}[/bold {t['secondary']}]",
            "API Calls:",
            f"[bold {t['secondary']}]{self._vitals_api_calls}[/bold {t['secondary']}]",
        )
        grid.add_row(
            "Cost:",
            f"[bold {t['success']}]${self._vitals_cost:.3f}[/bold {t['success']}]",
            "Elapsed:",
            f"[{t['warning']}]{self._fmt_elapsed(self._vitals_elapsed)}[/{t['warning']}]",
        )
        grid.add_row(
            "Screen:",
            f"[{t['dim']}]{self._vitals_resolution}[/{t['dim']}]",
            "Speed:",
            f"[bold {t['accent']}]{self._vitals_speed}[/bold {t['accent']}]",
        )

        return Panel(
            grid,
            title=f"[bold {t['vitals']}]📊 System Vitals[/bold {t['vitals']}]",
            border_style=t["vitals"],
            padding=(1, 2),
        )

    def _build_footer(self, t: dict) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(width=3)
        grid.add_column(ratio=1)
        grid.add_column(justify="right")

        grid.add_row(
            self.spinner,
            Text.from_markup(f"[bold {t['secondary']}]{self.status_message}[/bold {t['secondary']}]"),
            Text.from_markup(f"[{t['dim']}]Ctrl+C to abort[/{t['dim']}]"),
        )

        return Panel(grid, border_style=t["secondary"])
