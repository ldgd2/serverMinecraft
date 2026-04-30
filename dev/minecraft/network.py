import typer
import socket
import urllib.request
import re
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from dev.utils.core import console, print_header, print_success, print_info, print_error, update_env_variable

app = typer.Typer(help="Network utilities and configuration")

def get_public_ip():
    try:
        with urllib.request.urlopen("https://api64.ipify.org?format=text", timeout=3) as response:
            return response.read().decode("utf-8")
    except Exception:
        return None

def get_local_ip():
    try:
        # Connect to a dummy external IP to get the interface IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
        s.close()
        return IP
    except Exception:
        return "127.0.0.1"

@app.command("info")
def network_info():
    """Show network information (Local IP, Public IP, Hostname)."""
    hostname = socket.gethostname()
    local_ip = get_local_ip()
    public_ip = get_public_ip() or "Unavailable"

    console.print(Panel(
        f"[bold]Hostname:[/bold] {hostname}\n"
        f"[bold]Local Network IP:[/bold] [green]{local_ip}[/green]\n"
        f"[bold]Public IP:[/bold] [yellow]{public_ip}[/yellow]",
        title="Network Information",
        border_style="blue"
    ))

@app.command("configure")
def configure_network():
    """Interactive menu to configure Host and Port."""
    while True:
        console.clear()
        print_header("Network Configuration")
        console.print("1. Configure Host (IP)")
        console.print("2. Configure Port")
        console.print("3. View Info")
        console.print("0. Back")
        
        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "0"], default="1")
        
        if choice == "1":
            bind_host()
        elif choice == "2":
            bind_port()
        elif choice == "3":
            network_info()
            Prompt.ask("\nPress Enter to return...")
        elif choice == "0":
            break

@app.command("bind-host")
def bind_host():
    """Set the server HOST in .env file."""
    print_header("Configure Server Host")
    
    local_ip = get_local_ip()
    public_ip = get_public_ip()
    
    options = [
        {"name": "Localhost", "ip": "127.0.0.1", "desc": "Private, accessible only from this computer"},
        {"name": "Local Network", "ip": local_ip, "desc": "Accessible by devices on your WiFi/LAN"},
        {"name": "Any Interface", "ip": "0.0.0.0", "desc": "Listen on all interfaces (Recommended for access)"},
    ]
    
    if public_ip:
        options.append({"name": "Public IP", "ip": public_ip, "desc": "Requires Port Forwarding on router"})
    
    options.append({"name": "Custom IP", "ip": "custom", "desc": "Manually enter an IP"})

    for idx, opt in enumerate(options):
        console.print(f"[bold cyan]{idx + 1}. {opt['name']}[/bold cyan] ({opt['ip']})")
        console.print(f"   [dim]{opt['desc']}[/dim]")
    
    choice_idx = Prompt.ask("\nSelect Interface", choices=[str(i+1) for i in range(len(options))], default="2")
    selected = options[int(choice_idx) - 1]
    
    new_host = selected['ip']
    
    if new_host == "custom":
        new_host = Prompt.ask("Enter IP Address")
        # Basic validation
        if not re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", new_host) and new_host != "localhost":
             print_error("Invalid IP format")
             return

    update_env_variable("HOST", new_host)
    print_info(f"Server will listen on: {new_host}")
    Prompt.ask("\nPress Enter to continue...")

@app.command("bind-port")
def bind_port(port: str = None):
    """Set the server PORT in .env file."""
    if not port:
        print_header("Configure Server Port")
        console.print("Default: 8000")
        port = Prompt.ask("Enter Port Number", default="8000")
    
    if not port.isdigit():
        print_error("Port must be a number")
        return
        
    update_env_variable("PORT", port)
    Prompt.ask("\nPress Enter to continue...")

@app.command("scan-ports")
def scan_ports(target: str = "127.0.0.1", start_port: int = 25560, end_port: int = 25570):
    """Simple port scanner for a specific range."""
    console.print(f"Scanning {target} from port {start_port} to {end_port}...")
    for port in range(start_port, end_port + 1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((target, port))
        if result == 0:
            console.print(f"Port [green]{port}[/green]: [bold green]OPEN[/bold green]")
        sock.close()
