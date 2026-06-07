import re

with open("main.py", "r") as f:
    content = f.read()

# Add dashboard imports
import_str = """
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.rule import Rule
from rich.live import Live
from dashboard import LiveDashboard
"""
content = re.sub(r'from rich\.console import Console\nfrom rich\.panel import Panel\nfrom rich\.markdown import Markdown\nfrom rich\.text import Text\nfrom rich\.rule import Rule\n', import_str, content)

# Replace the execution loop
old_loop = """            console.print(f"\\n[bold magenta]► EXECUTING:[/bold magenta] {task}\\n")
            
            step_counter = 1
            status = console.status(f"[bold cyan]Initializing Step {step_counter}...[/bold cyan]", spinner="point")
            status.start()
            
            try:
                for event in agent.run(task):
                    if event["type"] == "status":
                        # Smooth update of the reasoning status
                        status.update(f"[bold cyan]{event['message']}[/bold cyan]")
                        
                    elif event["type"] == "action":
                        status.stop()
                        
                        thought = event.get('thought')
                        if thought:
                            console.print(Panel(Markdown(thought), title="[dim]Internal Reasoning[/dim]", border_style="dim blue"))
                            
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
                            
                        action_text = Text.assemble((icon, ""), (desc, ""), (" | ", "dim"), (target, ""))
                        console.print(Panel(action_text, title=f"[bold cyan]Action Executed (Step {step_counter})[/bold cyan]", border_style="cyan"))
                        
                        step_counter += 1
                        status.update(f"[bold cyan]Initializing Step {step_counter}...[/bold cyan]")
                        status.start()
                        
                    elif event["type"] == "complete":
                        status.stop()
                        thought = event.get('thought')
                        if thought:
                            console.print(Panel(Markdown(thought), title="[dim]Final Reasoning[/dim]", border_style="dim blue"))
                        console.print(Panel(f"✅ [bold green]TASK COMPLETE:[/bold green] {event.get('status')}", border_style="green", padding=(1, 2)))
                        
                    elif event["type"] == "error":
                        status.stop()
                        console.print(Panel(f"❌ [bold red]ERROR:[/bold red] {event['message']}", border_style="red"))
                        
                    elif event["type"] == "info":
                        status.stop()
                        console.print(Panel(f"ℹ️ [bold blue]INFO:[/bold blue]\\n{event['message']}", border_style="blue"))
                        
            finally:
                status.stop()"""

new_loop = """            
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
                pass"""

content = content.replace(old_loop, new_loop)

with open("main.py", "w") as f:
    f.write(content)

