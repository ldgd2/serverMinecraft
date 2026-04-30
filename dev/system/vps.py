import typer
import sys
import os
import subprocess
import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

app = typer.Typer(help="VPS and Ubuntu Services Manager")
console = Console()

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        while True:
            console.clear()
            console.print(Panel.fit("[bold magenta]🐧 VPS & Ubuntu Manager[/bold magenta]", border_style="magenta"))
            console.print("[1] Setup Systemd Service (Autostart API)")
            console.print("[2] Check VPS Status (RAM, Disk)")
            console.print("[3] View Service Logs")
            console.print("[4] Restart VPS Service")
            console.print("[5] System Update (apt update & upgrade)")
            console.print("[6] Firewall Setup (UFW)")
            console.print("[7] Network Ports (Listening)")
            console.print("[8] Top Processes (RAM usage)")
            console.print("[0] Return to Main Menu")
            
            choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5", "6", "7", "8", "0"], default="1")
            
            try:
                if choice == "1":
                    setup_service()
                elif choice == "2":
                    check_vps_status()
                elif choice == "3":
                    view_logs()
                elif choice == "4":
                    restart_service()
                elif choice == "5":
                    update_system()
                elif choice == "6":
                    setup_firewall()
                elif choice == "7":
                    check_ports()
                elif choice == "8":
                    top_processes()
                elif choice == "0":
                    break
            except Exception as e:
                console.print(f"[bold red]An error occurred: {e}[/bold red]")
            
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]")

@app.command("setup")
def setup_service():
    """Create and configure systemd service for Ubuntu"""
    if sys.platform == "win32":
        console.print("[bold red]Error: Systemd services can only be created on Linux (Ubuntu).[/bold red]")
        return
        
    console.print("[bold cyan]Setting up mine-manager.service...[/bold cyan]")
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    python_path = sys.executable
    user = Prompt.ask("Run service as user", default=os.getenv("USER", "root"))
    
    service_content = f"""[Unit]
Description=Minecraft Server Manager API
After=network.target

[Service]
User={user}
WorkingDirectory={project_root}
ExecStart={python_path} run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    
    service_path = "/etc/systemd/system/mine-manager.service"
    
    try:
        # Require sudo for this
        temp_file = "/tmp/mine-manager.service"
        with open(temp_file, "w") as f:
            f.write(service_content)
            
        console.print("[yellow]Requesting sudo to install service...[/yellow]")
        subprocess.run(["sudo", "mv", temp_file, service_path], check=True)
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
        subprocess.run(["sudo", "systemctl", "enable", "mine-manager.service"], check=True)
        
        start_now = Prompt.ask("Start the service now?", choices=["yes", "no"], default="yes")
        if start_now == "yes":
            subprocess.run(["sudo", "systemctl", "start", "mine-manager.service"], check=True)
            console.print("[bold green]✓ Service started successfully![/bold green]")
        else:
            console.print("[bold green]✓ Service installed and enabled on boot.[/bold green]")
            
    except Exception as e:
        console.print(f"[bold red]Failed to setup service: {e}[/bold red]")

@app.command("status")
def check_vps_status():
    """View overall VPS RAM and CPU status"""
    import psutil
    console.print(Panel("[bold cyan]VPS Status[/bold cyan]"))
    
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/') if sys.platform != 'win32' else psutil.disk_usage('.')
    
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")
    table.add_column("Total", justify="right")
    
    table.add_row("CPU", f"{cpu_usage}%", f"{psutil.cpu_count()} Cores")
    table.add_row("RAM", f"{memory.percent}%", f"{memory.total // (1024*1024)} MB")
    table.add_row("Disk", f"{disk.percent}%", f"{disk.total // (1024*1024*1024)} GB")
    
    console.print(table)

@app.command("logs")
def view_logs():
    """View systemd logs for the manager"""
    if sys.platform == "win32":
        console.print("[red]Not available on Windows.[/red]")
        return
        
    try:
        subprocess.run(["sudo", "journalctl", "-u", "mine-manager.service", "-n", "50", "--no-pager"])
    except Exception as e:
        console.print(f"[red]Failed to view logs: {e}[/red]")

@app.command("restart")
def restart_service():
    """Restart the systemd service"""
    if sys.platform == "win32":
        console.print("[red]Not available on Windows.[/red]")
        return
        
    try:
        console.print("[yellow]Restarting mine-manager.service...[/yellow]")
        subprocess.run(["sudo", "systemctl", "restart", "mine-manager.service"], check=True)
        console.print("[bold green]✓ Service restarted![/bold green]")
    except Exception as e:
        console.print(f"[red]Failed to restart service: {e}[/red]")

@app.command("update")
def update_system():
    """Update and upgrade Ubuntu packages"""
    if sys.platform == "win32":
        console.print("[red]Not available on Windows.[/red]")
        return
        
    try:
        console.print("[bold cyan]Updating package lists...[/bold cyan]")
        subprocess.run(["sudo", "apt", "update"], check=True)
        console.print("[bold cyan]Upgrading packages...[/bold cyan]")
        subprocess.run(["sudo", "apt", "upgrade", "-y"], check=True)
        console.print("[bold green]✓ System updated successfully![/bold green]")
    except Exception as e:
        console.print(f"[red]Failed to update system: {e}[/red]")

@app.command("firewall")
def setup_firewall():
    """Setup UFW Firewall with default Minecraft Manager rules"""
    if sys.platform == "win32":
        console.print("[red]Not available on Windows.[/red]")
        return
        
    try:
        console.print("[bold cyan]Configuring UFW Firewall...[/bold cyan]")
        rules = [
            ["sudo", "ufw", "allow", "22/tcp"],    # SSH
            ["sudo", "ufw", "allow", "80/tcp"],    # HTTP
            ["sudo", "ufw", "allow", "443/tcp"],   # HTTPS
            ["sudo", "ufw", "allow", "8000/tcp"],  # API Default
            ["sudo", "ufw", "allow", "25565/tcp"]  # Default Minecraft
        ]
        
        for rule in rules:
            subprocess.run(rule, check=True)
            
        subprocess.run(["sudo", "ufw", "enable"], check=True)
        subprocess.run(["sudo", "ufw", "status"], check=True)
        console.print("[bold green]✓ Firewall configured successfully![/bold green]")
    except Exception as e:
        console.print(f"[red]Failed to configure firewall: {e}[/red]")

@app.command("ports")
def check_ports():
    """View listening network ports"""
    if sys.platform == "win32":
        subprocess.run(["netstat", "-an", "|", "findstr", "LISTENING"], shell=True)
    else:
        try:
            console.print("[bold cyan]Listening Ports:[/bold cyan]")
            subprocess.run(["sudo", "ss", "-tuln"], check=True)
        except Exception as e:
            console.print(f"[red]Failed to check ports: {e}[/red]")

@app.command("top")
def top_processes():
    """View top memory consuming processes"""
    import psutil
    console.print(Panel("[bold cyan]Top 10 Memory Consuming Processes[/bold cyan]"))
    
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
        try:
            if proc.info['memory_percent'] is not None:
                processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
            
    # Sort by memory usage
    processes = sorted(processes, key=lambda p: p['memory_percent'], reverse=True)[:10]
    
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("PID", style="dim")
    table.add_column("Name")
    table.add_column("RAM %", justify="right")
    table.add_column("CPU %", justify="right")
    
    for p in processes:
        table.add_row(
            str(p['pid']), 
            p['name'], 
            f"{p['memory_percent']:.1f}%", 
            f"{p['cpu_percent']:.1f}%"
        )
        
    console.print(table)
