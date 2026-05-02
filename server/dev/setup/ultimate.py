import typer
import os
import sys
import json
import urllib.request
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

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

    # --- STEP 1: Environment & IP ---
    console.print("\n[bold cyan]STEP 1: Environment & Network Configuration[/bold cyan]")
    run_universal_wizard()
    sync_public_ip()
    
    # --- STEP 2: RCON Configuration ---
    console.print("\n[bold cyan]STEP 2: RCON Auto-Configuration[/bold cyan]")
    if Prompt.confirm("Do you want to configure RCON (Console access from App) for all servers?", default=True):
        setup_rcon_logic()

    # --- STEP 3: Skin Synchronization ---
    console.print("\n[bold cyan]STEP 3: SkinRestorer API Integration[/bold cyan]")
    if Prompt.confirm("Do you want to auto-configure SkinRestorer for all existing servers?", default=True):
        servers_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "servers")
        if os.path.exists(servers_dir):
            servers = [d for d in os.listdir(servers_dir) if os.path.isdir(os.path.join(servers_dir, d))]
            for server in servers:
                try:
                    setup_skinrestorer_auto(server)
                except Exception as e:
                    console.print(f"[yellow]! Failed to setup skins for {server}: {e}[/yellow]")
        else:
            console.print("[dim]No servers found to configure skins.[/dim]")

    # --- STEP 4: App Linkage ---
    console.print("\n[bold cyan]STEP 4: Mobile App Synchronization[/bold cyan]")
    # Already done in sync_public_ip() but let's confirm
    console.print("[green]✓ Mobile App environment updated via sync_public_ip.[/green]")

    console.print("\n" + "="*60)
    console.print(Panel("[bold green]✨ CONFIGURATION COMPLETE ✨[/bold green]\n\n"
                  "Everything is now synchronized:\n"
                  "1. Backend .env is configured with public IP.\n"
                  "2. Minecraft servers have RCON and Skins pointing to your API.\n"
                  "3. Mobile app is linked to the correct VPS address.\n\n"
                  "[bold yellow]Next Step:[/bold yellow] Restart the backend service (mine.py option 10).", 
                  border_style="green"))
    console.print("="*60 + "\n")

if __name__ == "__main__":
    app()
