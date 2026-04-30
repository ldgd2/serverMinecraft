import typer
import os
import sys
import subprocess
from rich.console import Console

app = typer.Typer(help="Run Database Seeders")
console = Console()

def run_seeder_script(filepath):
    console.print(f"Executing [cyan]{os.path.basename(filepath)}[/cyan]...")
    try:
        # Set PYTHONPATH to include project root so imports work correctly
        env = os.environ.copy()
        # Assuming this script is run from project root, or we need to find it relative to this file
        # The original code used __file__ of mine.py, which was in project root.
        # Here dev/seeder.py is one level deep.
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")
        
        # Run from project root directory
        subprocess.run([sys.executable, filepath], check=True, env=env, cwd=project_root)
        console.print(f"[green]✓ {os.path.basename(filepath)} completed.[/green]")
    except subprocess.CalledProcessError:
         console.print(f"[bold red]✗ Failed to run {os.path.basename(filepath)}[/bold red]")

@app.command("all")
def seeder_all():
    """
    Run all database seeders.
    """
    seeders_dir = os.path.join("database", "seeders")
    if not os.path.exists(seeders_dir):
        console.print("[red]Seeders directory not found![/red]")
        return

    console.print("[bold blue]Running all seeders...[/bold blue]")
    for filename in os.listdir(seeders_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            run_seeder_script(os.path.join(seeders_dir, filename))

@app.command("run")
def seeder_run(name: str):
    """
    Run a specific seeder by name (e.g., 'user_seeder').
    """
    seeders_dir = os.path.join("database", "seeders")
    target = os.path.join(seeders_dir, f"{name}.py")
    if os.path.exists(target):
        run_seeder_script(target)
    else:
         console.print(f"[red]Seeder '{name}' not found.[/red]")

@app.callback()
def main():
    pass
