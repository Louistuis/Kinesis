import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm

console = Console()

def run_setup_wizard():
    welcome_text = """
# Welcome to **Kinesis CLI**! 🚀
It looks like this is your first time launching Kinesis. Let's get everything set up so your AI agent can take control.
"""
    console.print(Panel(Markdown(welcome_text), border_style="cyan", padding=(1, 2)))
    
    # 1. API Key Setup
    console.print("\n[bold magenta]Step 1: Google Gemini API Key[/bold magenta]")
    console.print("Kinesis requires a Gemini API Key to function. You can get one for free at [cyan]https://aistudio.google.com/app/apikey[/cyan]")
    
    api_key = Prompt.ask("Enter your [bold yellow]GEMINI_API_KEY[/bold yellow]")
    if not api_key.strip():
        console.print("[red]API Key cannot be empty. Setup aborted.[/red]")
        sys.exit(1)
        
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    with open(env_path, "w") as f:
        f.write(f"GEMINI_API_KEY={api_key.strip()}\n")
    console.print(f"[green]✔ Saved API Key to {env_path}[/green]")
    
    # 2. Permissions Guide
    console.print("\n[bold magenta]Step 2: macOS Permissions[/bold magenta]")
    permissions_text = """
Kinesis needs low-level access to your Mac to see the screen and move the mouse.
Please ensure your Terminal app (or IDE) has the following permissions enabled in **System Settings > Privacy & Security**:
- ✅ **Accessibility** (To move the mouse and type)
- ✅ **Screen Recording** (To capture the screen for the AI)
"""
    console.print(Panel(Markdown(permissions_text), border_style="yellow"))
    Prompt.ask("[dim]Press Enter once you have granted these permissions...[/dim]")
    
    # 3. Alias Injection
    console.print("\n[bold magenta]Step 3: Global Alias[/bold magenta]")
    if Confirm.ask("Would you like to install the `kinesis` alias to your ~/.zshrc so you can run it from anywhere?"):
        zshrc_path = os.path.expanduser("~/.zshrc")
        kinesis_dir = os.path.dirname(os.path.abspath(__file__))
        alias_cmd = f'\nalias kinesis="cd {kinesis_dir} && {sys.executable} main.py"\n'
        
        try:
            with open(zshrc_path, "a") as f:
                f.write(alias_cmd)
            console.print("[green]✔ Added `kinesis` alias! Restart your terminal or run `source ~/.zshrc` to use it.[/green]")
        except Exception as e:
            console.print(f"[red]Failed to write alias: {e}[/red]")
    else:
        console.print("[dim]Skipped alias setup.[/dim]")
        
    # 4. Finalize
    setup_marker = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".setup_complete")
    with open(setup_marker, "w") as f:
        f.write("Setup complete.")
        
    success_text = """
# 🎉 Setup Complete!
Kinesis is now fully armed and operational. Proceeding to the main dashboard...
"""
    console.print(Panel(Markdown(success_text), border_style="green", padding=(1, 2)))
    import time
    time.sleep(2)
    console.clear()
    
if __name__ == "__main__":
    run_setup_wizard()
