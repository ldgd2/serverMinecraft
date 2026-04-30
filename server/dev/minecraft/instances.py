import typer
import sys
import os
import subprocess
import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

# Ensure parent is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

app = typer.Typer(help="Minecraft Server Instances Manager")
console = Console()

def get_servers():
    """Retrieve all server names from the servers/ directory"""
    servers_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "servers")
    if not os.path.exists(servers_dir):
        return []
    return [d for d in os.listdir(servers_dir) if os.path.isdir(os.path.join(servers_dir, d))]

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        while True:
            console.clear()
            console.print(Panel.fit("[bold green]🎮 Minecraft Instances Manager[/bold green]", border_style="green"))
            
            servers = get_servers()
            if not servers:
                console.print("[red]No Minecraft servers found in the 'servers/' directory.[/red]")
                Prompt.ask("Press Enter to exit")
                sys.exit(0)
                
            table = Table(show_header=True, header_style="bold yellow")
            table.add_column("ID", justify="center", style="cyan")
            table.add_column("Server Name", style="white")
            table.add_column("Latest Log Size", justify="right", style="dim")
            
            for idx, server in enumerate(servers):
                log_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "servers", server, "logs", "latest.log")
                log_size = f"{os.path.getsize(log_path) // 1024} KB" if os.path.exists(log_path) else "N/A"
                table.add_row(str(idx + 1), server, log_size)
                
            console.print(table)
            console.print("\n[bold cyan]Actions:[/bold cyan]")
            console.print("[1] View Live Logs (Tail)")
            console.print("[2] Force Kill (Emergency Stop)")
            console.print("[0] Return to Main Menu")
            
            action = Prompt.ask("\nSelect action", choices=["1", "2", "0"], default="1")
            
            if action == "0":
                break
                
            server_id = Prompt.ask("Select Server ID", choices=[str(i+1) for i in range(len(servers))])
            selected_server = servers[int(server_id) - 1]
            
            try:
                if action == "1":
                    tail_logs(selected_server)
                    # Skip the "Press Enter" prompt for logs to make it smoother
                    continue 
                elif action == "2":
                    force_kill(selected_server)
            except Exception as e:
                console.print(f"[bold red]An error occurred: {e}[/bold red]")
                
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]")

@app.command("logs")
def tail_logs(server_name: str):
    """Watch the live console logs of a specific server with rotation support"""
    console.print(f"[bold cyan]Watching logs for {server_name}... (Press Ctrl+C to exit)[/bold cyan]")
    log_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "servers", server_name, "logs", "latest.log")
    
    if not os.path.exists(log_path):
        # Try to wait a bit if server just started
        console.print("[yellow]Waiting for log file to be created...[/yellow]")
        for _ in range(5):
            if os.path.exists(log_path): break
            time.sleep(1)
            
    if not os.path.exists(log_path):
        console.print(f"[red]Error: Log file not found at {log_path}[/red]")
        return

    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            # Go to end of file
            f.seek(0, os.SEEK_END)
            
            while True:
                content = f.read()
                if content:
                    sys.stdout.write(content)
                    sys.stdout.flush()
                else:
                    # Check for rotation/truncation
                    if os.path.exists(log_path):
                        if os.path.getsize(log_path) < f.tell():
                            console.print("\n[yellow]Log file rotated/truncated, reopening...[/yellow]")
                            f.close()
                            f = open(log_path, "r", encoding="utf-8", errors="replace")
                            continue
                    
                    time.sleep(0.1)
                    
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopped watching logs.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error watching logs: {e}[/red]")

@app.command("kill")
def force_kill(server_name: str):
    """Force kill a frozen or unresponsive Minecraft server process"""
    import psutil
    console.print(f"[bold red]Attempting to force kill '{server_name}' processes...[/bold red]")
    
    killed = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline') or []
            # Check if it's a java process running this specific server's jar or path
            if 'java' in proc.info['name'].lower() and any(server_name in arg for arg in cmdline):
                proc.kill()
                killed += 1
                console.print(f"[green]Killed PID {proc.info['pid']}[/green]")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
            
    if killed > 0:
        console.print(f"[bold green]✓ Successfully terminated {killed} processes associated with {server_name}.[/bold green]")
    else:
        console.print("[yellow]No running processes found for this server.[/yellow]")
        
    time.sleep(2)
