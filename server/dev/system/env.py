import typer
import sys
import os
import re
import secrets
import string
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

# Ensure parent is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from dev.utils.core import update_env_variable

app = typer.Typer(help="Universal Environment Configurator")
console = Console()

def get_env_variable(key: str) -> str:
    """Reads a variable directly from the .env file if it exists."""
    env_path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(env_path):
        return None
    with open(env_path, "r") as f:
        content = f.read()
    pattern = re.compile(rf"^{key}\s*=\s*(.*)$", re.MULTILINE)
    match = pattern.search(content)
    if match:
        return match.group(1).strip()
    return None

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        while True:
            console.clear()
            console.print(Panel.fit("[bold cyan]Universal Environment Configurator[/bold cyan]", border_style="cyan"))
            console.print("[1] Run Universal Configurator (Interactive Wizard)")
            console.print("[2] Set a custom unlisted variable")
            console.print("[3] View current .env contents")
            console.print("[4] Auto-Sync Public IP (Detect and Update APP_URL)")
            console.print("[0] Return to Main Menu")
            
            choice = Prompt.ask("Select an option", choices=["1", "2", "3", "0"], default="1")
            
            try:
                if choice == "1":
                    run_universal_wizard()
                elif choice == "2":
                    key = Prompt.ask("Variable Name (e.g. CUSTOM_PORT)")
                    value = Prompt.ask("Value")
                    update_env_variable(key, value)
                elif choice == "3":
                    view_env()
                elif choice == "4":
                    sync_public_ip()
                elif choice == "0":
                    break
            except Exception as e:
                console.print(f"[bold red]An error occurred: {e}[/bold red]")
                
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]")

def run_universal_wizard():
    # Detect IP for default suggestion
    try:
        import urllib.request
        detected_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
    except:
        detected_ip = "127.0.0.1"

    console.print(Panel(
        "[bold yellow]Universal Configurator[/bold yellow]\n\n"
        "• Press [bold cyan]Enter[/bold cyan] without typing to [green]accept[/green] the default or keep the current value.\n"
        "• Type a new value to overwrite it.", border_style="yellow"
    ))
    
    settings = [
        {"key": "SECRET_KEY", "desc": "JWT Authentication Secret Key", "default": "<auto-generate-64-chars>"},
        {"key": "DB_HOST", "desc": "PostgreSQL Host", "default": "127.0.0.1"},
        {"key": "DB_PORT", "desc": "PostgreSQL Port", "default": "5432"},
        {"key": "DB_NAME", "desc": "PostgreSQL Database Name", "default": "mine_db"},
        {"key": "DB_USER", "desc": "PostgreSQL Username", "default": "postgres"},
        {"key": "DB_PASSWORD", "desc": "PostgreSQL Password", "default": "postgres"},
        {"key": "API_PORT", "desc": "Port for the FastAPI backend", "default": "8000"},
        {"key": "API_HOST", "desc": "Host for the FastAPI backend", "default": "0.0.0.0"},
        {"key": "PUBLIC_IP", "desc": "Public IP of the VPS", "default": detected_ip},
        {"key": "APP_URL", "desc": "Base URL (auto-generated from IP/Port)", "default": f"http://{detected_ip}:8000"},
        {"key": "DEFAULT_MINECRAFT_RAM", "desc": "Default RAM allocation for servers", "default": "4096M"},
        {"key": "DEFAULT_MINECRAFT_CORES", "desc": "Default CPU Cores for servers", "default": "6"},
    ]
    
    for s in settings:
        key = s["key"]
        desc = s["desc"]
        sys_default = s["default"]
        
        current_val = get_env_variable(key)
        
        if current_val is not None:
            # It already exists in .env
            prompt_str = f"[bold cyan]{key}[/bold cyan] [dim]({desc})[/dim]\n[yellow]Current: {current_val}[/yellow]\n[dim]New value (Enter to keep)[/dim]"
        else:
            # Doesn't exist, show system default
            prompt_str = f"[bold cyan]{key}[/bold cyan] [dim]({desc})[/dim]\n[green]Default: {sys_default}[/green]\n[dim]New value (Enter to use default)[/dim]"
            
        user_input = Prompt.ask(prompt_str, default="")
        
        if user_input == "":
            if current_val is None:
                # Use default
                if key == "SECRET_KEY" and sys_default == "<auto-generate-64-chars>":
                    alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_=+"
                    val_to_save = ''.join(secrets.choice(alphabet) for _ in range(64))
                else:
                    val_to_save = sys_default
                
                update_env_variable(key, val_to_save)
                # print_success handles the console print from update_env_variable, so we just add a visual spacer
                console.print("")
            else:
                # Keep current
                console.print(f"[dim]Kept existing value for {key}.[/dim]\n")
        else:
            # Save new value
            update_env_variable(key, user_input)
            console.print("")
            
    console.print("[bold green]✓ Universal Configuration complete![/bold green]")

def view_env():
    env_path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(env_path):
        console.print(Panel("[yellow]No .env file found currently.\nIt will be created automatically when you set a variable.[/yellow]"))
        return
        
    console.print(Panel(f"[bold cyan]Current contents of {env_path}:[/bold cyan]"))
    with open(env_path, "r") as f:
        content = f.read()
        if content.strip():
            console.print(content)
        else:
            console.print("[dim]File is empty.[/dim]")

def sync_public_ip():
    """Detects public IP and updates PUBLIC_IP and APP_URL in .env automatically."""
    console.print("[cyan]🔍 Detecting public IP...[/cyan]")
    try:
        import urllib.request
        public_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
        api_port = get_env_variable("API_PORT") or "8000"
        new_url = f"http://{public_ip}:{api_port}"
        
        console.print(f"[green]✓ Detected IP: {public_ip}[/green]")
        update_env_variable("PUBLIC_IP", public_ip)
        update_env_variable("APP_URL", new_url)
        console.print(f"[bold green]✓ .env updated: PUBLIC_IP={public_ip}, APP_URL={new_url}[/bold green]")
        
        # 3. Also update App (Flutter) .env if it exists
        # Relative path from server/ to appserve/
        app_env_path = os.path.abspath(os.path.join(os.getcwd(), "..", "appserve", ".env"))
        if os.path.exists(app_env_path):
            try:
                with open(app_env_path, "r") as f:
                    app_content = f.read()
                
                # Update API_URL in Flutter env
                new_api_url = f"{new_url}/api/v1"
                if "API_URL=" in app_content:
                    app_content = re.sub(r"^API_URL=.*$", f"API_URL={new_api_url}", app_content, flags=re.MULTILINE)
                else:
                    app_content += f"\nAPI_URL={new_api_url}\n"
                
                with open(app_env_path, "w") as f:
                    f.write(app_content)
                console.print(f"[bold green]✓ App .env updated: API_URL={new_api_url}[/bold green]")
            except Exception as e_app:
                console.print(f"[yellow]! Could not update App .env: {e_app}[/yellow]")
        
        console.print("[dim]Note: You might need to restart the backend and rebuild the App to apply changes.[/dim]")
    except Exception as e:
        console.print(f"[bold red]Failed to sync IP: {e}[/bold red]")
