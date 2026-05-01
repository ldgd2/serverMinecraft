import typer
import sys
import os
import importlib.util
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.layout import Layout
from rich.live import Live
from rich.align import Align
from rich.text import Text
from rich import box
import secrets
import string
import time

app = typer.Typer(help="Minecraft Server Manager CLI Tool")
console = Console()

# --- Recursive Dynamic Loader ---
def load_commands():
    """Dynamically load commands from the 'dev' package and its subdirectories."""
    dev_dir = os.path.join(os.path.dirname(__file__), "dev")
    if not os.path.exists(dev_dir):
        return

    for root, dirs, files in os.walk(dev_dir):
        for filename in files:
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                
                # We extract the package name relative to dev dir
                rel_path = os.path.relpath(root, dev_dir)
                if rel_path == ".":
                    pkg_path = f"dev.{module_name}"
                else:
                    pkg_path = f"dev.{rel_path.replace(os.sep, '.')}.{module_name}"
                    
                file_path = os.path.join(root, filename)
                
                try:
                    spec = importlib.util.spec_from_file_location(pkg_path, file_path)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        sys.modules[pkg_path] = module
                        spec.loader.exec_module(module)
                        
                        if hasattr(module, "app"):
                            # To avoid naming collisions between packages (e.g. database/manager.py and vps/manager.py)
                            # we name the command group as package_module, e.g. "database" or "vps"
                            # If the file is "manager.py", we use the folder name as the command name.
                            cmd_name = module_name
                            if module_name in ["manager", "core"]:
                                cmd_name = os.path.basename(root)
                            app.add_typer(module.app, name=cmd_name)
                except Exception as e:
                    console.print(f"[dim red]Failed to load module {pkg_path}: {e}[/dim red]")

load_commands()

@app.command()
def generate_secret(length: int = typer.Option(64, help="Length of the secret key (min 32)")):
    """Generate a secure SECRET_KEY for JWT authentication."""
    if length < 32:
        console.print("[red]Error: Minimum length is 32 bytes for HS256[/red]")
        sys.exit(1)
    
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_=+"
    secret_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    env_file = ".env"
    new_line = f"SECRET_KEY={secret_key}"
    
    try:
        if not os.path.exists(env_file):
            # Create .env if it doesn't exist
            with open(env_file, "w") as f:
                f.write(new_line + "\n")
            console.print("[green]✓ Created .env file and added SECRET_KEY![/green]")
        else:
            with open(env_file, "r") as f:
                lines = f.readlines()
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith("SECRET_KEY="):
                    lines[i] = new_line + "\n"
                    updated = True
                    break
            if not updated:
                lines.insert(0, new_line + "\n")
            with open(env_file, "w") as f:
                f.writelines(lines)
            console.print("[green]✓ .env file updated successfully![/green]")
    except Exception as e:
        console.print(f"[red]Error modifying .env: {e}[/red]")
        sys.exit(1)
    
    console.print(Panel(f"[bold green]Generated SECRET_KEY:[/bold green]\n\n{secret_key}", title="🔐 Secure Secret Key", border_style="green", expand=False))

# --- Beautiful Interactive Menu ---

@app.callback(invoke_without_command=True)
def main_interactive(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        show_animated_welcome()
        show_menu()

def show_animated_welcome():
    console.clear()
    title = Text("Minecraft Server Manager CLI", justify="center", style="bold cyan")
    subtitle = Text("Initializing the ultimate management experience...", justify="center", style="dim")
    
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    
    layout["header"].update(Panel(title, border_style="blue", box=box.ROUNDED))
    layout["main"].update(Align.center(Text("\n\n\n\nLoading modules...", style="bold magenta")))
    layout["footer"].update(Panel(subtitle, border_style="dim", box=box.ROUNDED))
    
    with Live(layout, refresh_per_second=10, screen=True):
        time.sleep(0.5)
        layout["main"].update(Align.center(Text("\n\n\n\nConnecting to databases...", style="bold blue")))
        time.sleep(0.5)
        layout["main"].update(Align.center(Text("\n\n\n\nReady.", style="bold green")))
        time.sleep(0.3)

def show_menu():
    while True:
        console.clear()
        console.print(Panel.fit(
            "[bold cyan]🚀 MINECRAFT SERVER MANAGER CLI 🚀[/bold cyan]\n[white]Select a module to proceed.[/white]",
            border_style="magenta",
            box=box.DOUBLE
        ))

        table = Table(show_header=True, header_style="bold yellow", box=box.SIMPLE_HEAVY, expand=True)
        table.add_column("No.", style="bold cyan", width=4, justify="center")
        table.add_column("Package", style="bold green", width=15)
        table.add_column("Action", style="white")
        table.add_column("Description", style="dim")

        table.add_row("1", "Server", "Start (Dev)", "Run development API server")
        table.add_row("2", "Database", "Manager", "Initialize DB, Passwords, Migrations")
        table.add_row("3", "System/VPS", "Manager", "Ubuntu setup, Services, Performance, Firewall")
        table.add_row("4", "Maintenance", "Clean/Check", "Clean logs, check disk")
        table.add_row("5", "Minecraft", "Config", "Manage properties, networks")
        table.add_row("6", "Minecraft", "Instances", "View logs, start/stop servers directly")
        table.add_row("7", "System", "Environment", "Configure .env file dynamically")
        table.add_row("8", "Auth", "Create User", "Create administrator users")
        table.add_row("9", "Security", "Generate JWT", "Generate new secret key")
        table.add_row("10", "System", "Restart", "Restart Backend Service")
        table.add_row("11", "System", "Status", "Check Service Status")
        table.add_row("12", "Security", "Key Manager", "Generate/View Admin API Keys")
        table.add_row("0", "Exit", "Quit", "Close the CLI")
        
        console.print(table)
        console.print("\n")

        choice = Prompt.ask("[bold yellow]❯ Select an option[/bold yellow]", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "0"], default="1")
        import subprocess
        script_path = os.path.abspath(__file__)
        python_exe = sys.executable

        if choice == "1":
            subprocess.run([python_exe, script_path, "server", "run"])
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
        elif choice == "2":
            subprocess.run([python_exe, script_path, "database"])
        elif choice == "3":
            subprocess.run([python_exe, script_path, "vps"])
        elif choice == "4":
            subprocess.run([python_exe, script_path, "maintenance"])
        elif choice == "5":
            subprocess.run([python_exe, script_path, "properties"])
        elif choice == "6":
            subprocess.run([python_exe, script_path, "instances"])
        elif choice == "7":
            subprocess.run([python_exe, script_path, "env"])
        elif choice == "8":
            subprocess.run([python_exe, script_path, "users"])
        elif choice == "9":
            length = Prompt.ask("Key length (min 32)", default="64")
            subprocess.run([python_exe, script_path, "generate-secret", "--length", length])
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
        elif choice == "10":
            subprocess.run([python_exe, script_path, "vps", "restart"])
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
        elif choice == "11":
            subprocess.run([python_exe, script_path, "vps", "status"])
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
        elif choice == "12":
            subprocess.run([python_exe, script_path, "security"])
        elif choice == "0":
            console.print("[bold cyan]Goodbye![/bold cyan]")
            sys.exit(0)

if __name__ == "__main__":
    app()
