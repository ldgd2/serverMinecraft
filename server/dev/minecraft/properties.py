import typer
import os
from rich.console import Console
from rich.table import Table
import json
import urllib.request

app = typer.Typer(help="Manage server.properties configuration")
console = Console()

DEFAULT_PROPERTIES_FILE = "server.properties"

def load_properties(file_path: str):
    """Parses a server.properties file into a dictionary."""
    props = {}
    if not os.path.exists(file_path):
        return props
    
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                props[key.strip()] = value.strip()
    return props

def save_properties(file_path: str, props: dict):
    """Saves a dictionary of properties back to the file."""
    lines = []
    # Read original lines to preserve comments if possible, but for now simple overwrite
    # To do it properly, we'd read, modify in place. 
    # specific implementation: Read all lines, if key found replace, else append.
    
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            lines = f.readlines()
    
    new_lines = []
    keys_written = set()
    
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in props:
                new_lines.append(f"{key}={props[key]}\n")
                keys_written.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    # Append new keys
    for key, value in props.items():
        if key not in keys_written:
            new_lines.append(f"{key}={value}\n")
            
    with open(file_path, "w") as f:
        f.writelines(new_lines)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        from rich.prompt import Prompt
        from rich.panel import Panel
        
        while True:
            console.clear()
            console.print(Panel.fit("[bold yellow]⚙️ Properties Configurator[/bold yellow]", border_style="yellow"))
            console.print("[1] List Properties")
            console.print("[2] Get Specific Property")
            console.print("[3] Set Property")
            console.print("[4] Bind to Localhost (127.0.0.1)")
            console.print("[5] Bind to Public (0.0.0.0)")
            console.print("[6] Auto-Config SkinRestorer")
            console.print("[0] Return to Main Menu")
            
            choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5", "0"], default="1")
            
            # Select Server First
            servers_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")), "servers")
            if not os.path.exists(servers_dir):
                os.makedirs(servers_dir, exist_ok=True)
                
            servers = [d for d in os.listdir(servers_dir) if os.path.isdir(os.path.join(servers_dir, d))]
            if not servers and choice != "0":
                console.print("[red]No servers found. Please create a server first from the Web API or Dashboard.[/red]")
                Prompt.ask("\n[dim]Press Enter to continue...[/dim]")
                continue
                
            if choice == "0":
                break
                
            console.print("\n[bold cyan]Available Servers:[/bold cyan]")
            for idx, server in enumerate(servers):
                console.print(f"[{idx+1}] {server}")
            
            srv_choice = Prompt.ask("Select Server ID", choices=[str(i+1) for i in range(len(servers))])
            selected_server = servers[int(srv_choice) - 1]
            prop_file = os.path.join(servers_dir, selected_server, "server.properties")
            
            try:
                if choice == "1":
                    list_properties(prop_file)
                elif choice == "2":
                    key = Prompt.ask("Key")
                    get_property(key, prop_file)
                elif choice == "3":
                    key = Prompt.ask("Key")
                    val = Prompt.ask("Value")
                    set_property(key, val, prop_file)
                elif choice == "4":
                    bind_local(prop_file)
                elif choice == "5":
                    bind_public(prop_file)
                elif choice == "6":
                    setup_skinrestorer_auto(selected_server)
            except Exception as e:
                console.print(f"[bold red]An error occurred: {e}[/bold red]")
                
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]")

@app.command("list")
def list_properties(file: str = typer.Option(DEFAULT_PROPERTIES_FILE, help="Path to server.properties")):
    """List all properties in the file."""
    if not os.path.exists(file):
        console.print(f"[red]File {file} not found.[/red]")
        return

    props = load_properties(file)
    table = Table(title=f"Properties in {file}")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    
    for k, v in props.items():
        table.add_row(k, v)
        
    console.print(table)

@app.command("get")
def get_property(key: str, file: str = typer.Option(DEFAULT_PROPERTIES_FILE, help="Path to server.properties")):
    """Get a specific property value."""
    props = load_properties(file)
    if key in props:
        console.print(f"[bold]{key}[/bold] = [green]{props[key]}[/green]")
    else:
        console.print(f"[yellow]Property '{key}' not found.[/yellow]")

@app.command("set")
def set_property(key: str, value: str, file: str = typer.Option(DEFAULT_PROPERTIES_FILE, help="Path to server.properties")):
    """Set a property value."""
    props = {key: value}
    save_properties(file, props)
    console.print(f"[green]Set {key}={value} in {file}[/green]")

@app.command("set-port")
def set_port(port: int, file: str = typer.Option(DEFAULT_PROPERTIES_FILE, help="Path to server.properties")):
    """Shortcut to set server-port."""
    set_property("server-port", str(port), file)

@app.command("bind-local")
def bind_local(file: str = typer.Option(DEFAULT_PROPERTIES_FILE, help="Path to server.properties")):
    """Bind server to 127.0.0.1 (Localhost only)."""
    set_property("server-ip", "127.0.0.1", file)

@app.command("bind-public")
def bind_public(file: str = typer.Option(DEFAULT_PROPERTIES_FILE, help="Path to server.properties")):
    """Bind server to 0.0.0.0 (Publicly accessible)."""
    set_property("server-ip", "0.0.0.0", file)

@app.command("bind")
def bind(ip: str, file: str = typer.Option(DEFAULT_PROPERTIES_FILE, help="Path to server.properties")):
    """Bind server to a specific IP."""
    set_property("server-ip", ip, file)

def setup_minebridge_mod_auto(server_name: str, app_url: str):
    """Configures the MineBridge mod minebridge.json with API keys and Backend URL."""
    console.print(f"[cyan]⚙️  Configuring MineBridge Mod for {server_name}...[/cyan]")
    
    # 1. Get an API Key from DB
    from database.connection import SessionLocal
    from database.models.user import User
    from dev.security.manager import get_fernet
    
    db = SessionLocal()
    api_key = "PENDING"
    try:
        # Find first admin with a key
        admin = db.query(User).filter(User.is_admin == True, User.api_key_encrypted != None).first()
        if admin:
            f = get_fernet()
            api_key = f.decrypt(admin.api_key_encrypted.encode()).decode()
        else:
            # Generate one for the first admin if none exists
            admin = db.query(User).filter(User.is_admin == True).first()
            if admin:
                import secrets
                import hashlib
                raw_key = secrets.token_urlsafe(32)
                f = get_fernet()
                admin.api_key_encrypted = f.encrypt(raw_key.encode()).decode()
                admin.api_key_hashed = hashlib.sha256(raw_key.encode()).hexdigest()
                db.commit()
                api_key = raw_key
                console.print("[yellow]! No API Key found. Generated a new one for admin.[/yellow]")
    except Exception as e:
        console.print(f"[red]! Error retrieving API key: {e}[/red]")
    finally:
        db.close()

    # 2. Path to minebridge.json
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    config_dir = os.path.join(base_dir, "servers", server_name, "config")
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "minebridge.json")

    # 3. Write Config
    try:
        import json
        config = {
            "backend_url": app_url,
            "api_key": api_key,
            "server_ip": "auto",
            "server_name": server_name
        }
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        console.print(f"[bold green]✓ MineBridge Mod configured for {server_name}![/bold green]")
    except Exception as e:
        console.print(f"[red]! Failed to write minebridge.json: {e}[/red]")

@app.command("setup-skins")
def setup_skinrestorer_auto(server_name: str):
    """Detects public IP and configures SkinRestorer for the specified server."""
    console.print(f"[cyan]🚀 Auto-configuring skins for {server_name}...[/cyan]")
    
    # 1. Get Base URL from .env
    from dev.system.env import get_env_variable
    api_host = get_env_variable("API_HOST")
    api_port = get_env_variable("API_PORT") or "8000"
    
    if api_host:
        if api_host == "0.0.0.0":
            # Fallback to auto-detection if it's just binding all
            try:
                public_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
                app_url = f"http://{public_ip}:{api_port}"
                console.print(f"[yellow]! API_HOST is 0.0.0.0. Using detected public IP: {public_ip}[/yellow]")
            except:
                app_url = f"http://127.0.0.1:{api_port}"
                console.print("[red]! Could not detect IP. Falling back to localhost.[/red]")
        else:
            app_url = f"http://{api_host}:{api_port}"
    else:
        # Compatibility check for legacy APP_URL if still present
        app_url = get_env_variable("APP_URL")
        if not app_url:
            # Full fallback
            try:
                public_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
                app_url = f"http://{public_ip}:{api_port}"
                console.print(f"[yellow]! API_HOST not found. Using detected IP: {public_ip}[/yellow]")
            except:
                app_url = f"http://127.0.0.1:{api_port}"
                console.print("[red]! Could not detect IP. Falling back to localhost.[/red]")

    # 2. Path to config.json
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    config_path = os.path.join(base_dir, "servers", server_name, "config", "skinrestorer", "config.json")
    
    if not os.path.exists(config_path):
        console.print(f"[red]Error: {config_path} not found. Is SkinRestorer installed on this server?[/red]")
        return

    # 3. Load and Update JSON
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        
        # Disable autoFetch to prevent SkinRestorer from failing and showing errors
        # Our MineBridge mod already handles the injection on join.
        config["join"] = config.get("join", {})
        config["join"]["autoFetch"] = {
            "enabled": False, 
            "provider": "mojang" # Set to default to avoid "not registered" warnings even if disabled
        }
        
        # Super-Robust SkinRestorer Configuration (Fabric 1.21 Compatible)
        # Ensure 'customProviders' is correctly structured as a map
        if "customProviders" not in config:
            config["customProviders"] = {}
            
        config["customProviders"]["MineManager"] = {
            "type": "WEB",
            "url": f"{app_url}/api/v1/players/skin/%s"
        }

        # Also ensure it's in the generic providers list for compatibility
        if "providers" not in config:
            config["providers"] = {}
        
        config["providers"]["MineManager"] = {
            "enabled": True,
            "type": "CUSTOM",
            "customName": "MineManager"
        }
        
        # Disable built-in providers to avoid redundant lookups
        for p in ["mojang", "ely_by", "mineskin"]:
            if p in config["providers"]:
                config["providers"][p]["enabled"] = False

        # --- DATABASE SYNC: Force SkinRestorer to use our PostgreSQL ---
        try:
            db_host = os.environ.get("DB_HOST", "localhost")
            db_port = int(os.environ.get("DB_PORT", 5432))
            db_name = os.environ.get("DB_NAME", "mine_db")
            db_user = os.environ.get("DB_USER", "postgres")
            db_pass = os.environ.get("DB_PASSWORD", "")

            config["storage"] = {
                "type": "POSTGRESQL",
                "host": db_host,
                "port": db_port,
                "database": db_name,
                "username": db_user,
                "password": db_pass
            }
            console.print(f"[dim]✓ SkinRestorer Storage synced with PostgreSQL ({db_host})[/dim]")
        except Exception as db_err:
            console.print(f"[yellow]! Could not auto-sync DB config: {db_err}[/yellow]")
        
        # Save
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
            
        console.print(f"[bold green]✓ SkinRestorer configured successfully in {server_name}![/bold green]")
        console.print(f"[dim]Provider: MineManager -> {app_url}[/dim]")
        
        # 4. Also setup MineBridge Mod Config
        # If LOCAL_MOD_COMM is true, the mod (running on this VPS) should talk to localhost
        is_local = get_env_variable("LOCAL_MOD_COMM")
        if is_local and is_local.lower() == "true":
            mod_app_url = f"http://127.0.0.1:{api_port}"
            console.print(f"[yellow]! LOCAL_MOD_COMM is enabled. Mod will use: {mod_app_url}[/yellow]")
        else:
            mod_app_url = app_url
            
        setup_minebridge_mod_auto(server_name, mod_app_url)
        
    except Exception as e:
        console.print(f"[bold red]Error updating JSON: {e}[/bold red]")
