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
    
    # 1. Authentication Setup
    console.print("\n[bold magenta]Step 1: Authentication Method[/bold magenta]")
    
    auth_choice = Prompt.ask(
        "Choose your authentication method:\n"
        "[1] API Key (Recommended for most users)\n"
        "[2] OAuth (Auto-detect existing Gemini CLI / gcloud credentials)\n"
        "[3] OAuth (Interactive Setup via URL)\n"
        "Enter 1, 2, or 3", 
        choices=["1", "2", "3"], 
        default="1"
    )
    
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    
    if auth_choice == "1":
        existing_key = os.environ.get("GEMINI_API_KEY")
        api_key = ""
        
        if existing_key:
            masked_key = f"{existing_key[:4]}...{existing_key[-4:]}" if len(existing_key) > 8 else "***"
            console.print(f"[green]Auto-detected an existing GEMINI_API_KEY in your environment: {masked_key}[/green]")
            if Confirm.ask("Would you like to use this existing key?"):
                api_key = existing_key
                
        if not api_key:
            console.print("Kinesis requires a Gemini API Key to function. You can get one for free at [cyan]https://aistudio.google.com/app/apikey[/cyan]")
            api_key = Prompt.ask("Enter your [bold yellow]GEMINI_API_KEY[/bold yellow]")
            
        if not api_key or not api_key.strip():
            console.print("[red]API Key cannot be empty. Setup aborted.[/red]")
            sys.exit(1)
            
        with open(env_path, "w") as f:
            f.write(f"GEMINI_AUTH_MODE=apikey\nGEMINI_API_KEY={api_key.strip()}\n")
        console.print(f"[green]✔ Saved API Key to {env_path}[/green]")
        
    elif auth_choice == "2":
        console.print("\n[yellow]OAuth Auto-Detect Mode Selected.[/yellow]")
        console.print("Kinesis will use your local Application Default Credentials (ADC).")
        with open(env_path, "w") as f:
            f.write("GEMINI_AUTH_MODE=oauth\n")
        console.print(f"[green]✔ Saved OAuth Mode to {env_path}[/green]")
        
    elif auth_choice == "3":
        console.print("\n[yellow]OAuth Interactive Setup Selected.[/yellow]")
        if os.system("command -v gcloud > /dev/null") != 0:
            console.print("[red]❌ Error: Google Cloud CLI (gcloud) is not installed on your system.[/red]")
            console.print("Please install it first: [cyan]https://cloud.google.com/sdk/docs/install[/cyan]")
            console.print("Or run the wizard again and choose API Key authentication.")
            sys.exit(1)
            
        console.print("Launching gcloud interactive authentication...")
        ret = os.system("gcloud auth application-default login --no-browser")
        if ret != 0:
            console.print("[red]❌ OAuth login failed or was cancelled.[/red]")
            sys.exit(1)
            
        with open(env_path, "w") as f:
            f.write("GEMINI_AUTH_MODE=oauth\n")
        console.print(f"[green]✔ Saved OAuth Mode to {env_path}[/green]")
        
    # Verify Credentials Live
    console.print("\n[dim]Verifying Gemini API access...[/dim]")
    try:
        from google import genai
        # Force reload env to pick up the newly written file
        from dotenv import load_dotenv
        load_dotenv(env_path, override=True)
        
        if os.environ.get("GEMINI_AUTH_MODE") == "oauth":
            client = genai.Client()
        else:
            client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
            
        # Light ping to verify auth
        client.models.get(model="gemini-3-flash-preview")
        console.print("[green]✔ Authentication verified successfully![/green]")
    except Exception as e:
        console.print(f"[red]❌ Authentication Verification Failed:[/red] {e}")
        console.print("[yellow]Please run the setup wizard again to fix your credentials.[/yellow]")
        if os.path.exists(env_path):
            os.remove(env_path) # Clean up invalid config
        sys.exit(1)
    
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
        kinesis_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
    setup_marker = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".setup_complete")
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
