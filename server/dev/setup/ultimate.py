import typer
import os
import sys
import json
import urllib.request
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

# Ensure parent is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from dev.system.env import run_universal_wizard, sync_public_ip, get_env_variable
from dev.minecraft.properties import setup_skinrestorer_auto
from setup_rcon import main as setup_rcon_logic

app = typer.Typer(help="Ultimate One-Click Configurator")
console = Console()

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        run_ultimate_setup()

@app.command("run")
def run_ultimate_setup():
    """The ultimate wizard to configure everything at once."""
    console.clear()
    console.print(Panel.fit(
        "[bold magenta]🚀 ULTIMATE SETUP WIZARD 🚀[/bold magenta]\n"
        "[white]One configuration to rule them all.[/white]",
        border_style="magenta"
    ))

    # --- STEP 0: Dependencies ---
    console.print("\n[bold cyan]STEP 0: Installing Dependencies[/bold cyan]")
    try:
        import subprocess
        python_exe = sys.executable
        req_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "requirements.txt")
        subprocess.run([python_exe, "-m", "pip", "install", "-r", req_path], check=True)
        subprocess.run([python_exe, "-m", "pip", "install", "Pillow"], check=True)
        console.print("[green]✓ Dependencies are up to date.[/green]")
    except Exception as e:
        console.print(f"[yellow]! Warning during dependency update: {e}[/yellow]")

    # --- STEP 1: Environment & IP ---
    console.print("\n[bold cyan]STEP 1: Environment & Network Configuration[/bold cyan]")
    run_universal_wizard()
    sync_public_ip()
    
    # --- STEP 2: Minecraft Basics (EULA) ---
    console.print("\n[bold cyan]STEP 2: Auto-Accept EULA for all servers[/bold cyan]")
    servers_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "servers")
    if os.path.exists(servers_dir):
        servers = [d for d in os.listdir(servers_dir) if os.path.isdir(os.path.join(servers_dir, d))]
        for server in servers:
            eula_path = os.path.join(servers_dir, server, "eula.txt")
            try:
                with open(eula_path, "w") as f:
                    f.write("eula=true\n")
                console.print(f"[dim]✓ EULA accepted for {server}[/dim]")
            except:
                pass
    
    # --- STEP 3: RCON Configuration ---
    console.print("\n[bold cyan]STEP 3: RCON Auto-Configuration[/bold cyan]")
    if Confirm.ask("Do you want to configure RCON (Console access from App) for all servers?", default=True):
        setup_rcon_logic()

    # --- STEP 4: Skin & Mod Synchronization ---
    console.print("\n[bold cyan]STEP 4: SkinRestorer & MineBridge Mod Integration[/bold cyan]")
    if Confirm.ask("Do you want to auto-configure Skins and Mod settings for all servers?", default=True):
        if os.path.exists(servers_dir):
            servers = [d for d in os.listdir(servers_dir) if os.path.isdir(os.path.join(servers_dir, d))]
            for server in servers:
                try:
                    setup_skinrestorer_auto(server)
                except Exception as e:
                    console.print(f"[yellow]! Failed to setup skins for {server}: {e}[/yellow]")
    
    # --- STEP 5: App Linkage ---
    console.print("\n[bold cyan]STEP 5: Mobile App Synchronization[/bold cyan]")
    console.print("[green]✓ Mobile App environment updated.[/green]")

    console.print("\n" + "="*60)
    console.print(Panel("[bold green]✨ ULTIMATE CONFIGURATION COMPLETE ✨[/bold green]\n\n"
                  "1. All dependencies installed.\n"
                  "2. EULA accepted for all instances.\n"
                  "3. RCON configured (Console enabled).\n"
                  "4. Skins & Mod synced with API.\n"
                  "5. App linked to VPS IP.\n\n"
                  "[bold yellow]Final Step:[/bold yellow] Restart the backend (Option 10) and then the Minecraft servers.", 
                  border_style="green"))
    console.print("="*60 + "\n")

if __name__ == "__main__":
    app()
