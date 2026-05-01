import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
import secrets
import base64
import os
from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.models.user import User
from app.services.auth_service import verify_password
from cryptography.fernet import Fernet
import hashlib
from rich import box

app = typer.Typer(help="Security & API Key Management")
console = Console()

def get_fernet():
    """Genera un objeto Fernet basado en el SECRET_KEY del sistema."""
    secret = os.getenv("SECRET_KEY", "default-secret-change-me-for-security")
    key = hashlib.sha256(secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))

def verify_admin_access(db, username):
    """Auxiliary function to verify if the user exists and the password is correct."""
    user = db.query(User).filter(User.username == username, User.is_admin == True).first()
    if not user:
        console.print(f"[red]Error: User '{username}' not found or is not an administrator.[/red]")
        return None
    
    password = Prompt.ask(f"[bold cyan]Confirm password for administrator '{username}'[/bold cyan]", password=True)
    if not verify_password(password, user.hashed_password):
        console.print("[red]❌ Access Denied: Incorrect password.[/red]")
        return None
    
    return user

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Interactive Security Management Menu with mandatory verification"""
    if ctx.invoked_subcommand is None:
        while True:
            console.clear()
            console.print(Panel.fit(
                "[bold yellow]🔐 SECURE API KEY MANAGEMENT[/bold yellow]", 
                border_style="yellow", 
                box=box.DOUBLE,
                subtitle="Password verification required for all actions"
            ))
            
            console.print("[1] [bold green]Generate New API Key[/bold green]")
            console.print("[2] [bold cyan]List Active API Keys[/bold cyan]")
            console.print("[3] [bold blue]View/Reveal API Key[/bold blue]")
            console.print("[4] [bold red]Revoke/Delete API Key[/bold red]")
            console.print("\n[0] Return to Main Menu")
            
            choice = Prompt.ask("\n❯ Select an option", choices=["1", "2", "3", "4", "0"], default="1")
            
            if choice == "1":
                username = Prompt.ask("Enter administrator username")
                generate_key_cmd(username)
            elif choice == "2":
                list_keys_cmd()
            elif choice == "3":
                username = Prompt.ask("Enter username to reveal key")
                show_key_cmd(username)
            elif choice == "4":
                username = Prompt.ask("Enter username to revoke key")
                delete_key_cmd(username)
            elif choice == "0":
                break
                
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]")

@app.command("generate")
def generate_key_cmd(username: str):
    """Generate a secure API Key after verifying identity."""
    db: Session = SessionLocal()
    try:
        user = verify_admin_access(db, username)
        if not user: return
 
        raw_key = secrets.token_urlsafe(32)
        f = get_fernet()
        user.api_key_encrypted = f.encrypt(raw_key.encode()).decode()
        user.api_key_hashed = hashlib.sha256(raw_key.encode()).hexdigest()
        db.commit()
 
        console.print(Panel(
            f"[bold green]API Key successfully generated for {username}![/bold green]\n\n"
            f"KEY: [bold yellow]{raw_key}[/bold yellow]\n\n"
            "[red]IMPORTANT:[/red] This key will only be shown once now.\n"
            "[dim]The key is stored encrypted. Use it in /minebridge set-key.[/dim]",
            title="🔑 SECURE KEY GENERATION",
            border_style="green"
        ))
    finally:
        db.close()

@app.command("list")
def list_keys_cmd():
    """List all administrators who have an API Key."""
    db: Session = SessionLocal()
    try:
        users = db.query(User).filter(User.api_key_encrypted != None).all()
        if not users:
            console.print("[yellow]No active API Keys found in the system.[/yellow]")
            return
 
        table = Table(title="Authorized API Access", border_style="cyan", box=box.ROUNDED)
        table.add_column("Username", style="bold green")
        table.add_column("Status", style="magenta")
        table.add_column("Encrypted Storage", style="dim")
 
        for u in users:
            table.add_row(u.username, "🟢 ACTIVE", "YES (AES-256)")
 
        console.print(table)
    finally:
        db.close()

@app.command("show")
def show_key_cmd(username: str):
    """View an existing API Key after verifying identity."""
    db: Session = SessionLocal()
    try:
        user = verify_admin_access(db, username)
        if not user: return
        
        if not user.api_key_encrypted:
            console.print(f"[yellow]User '{username}' does not have an API Key.[/yellow]")
            return
 
        # Desencriptar
        f = get_fernet()
        decrypted_key = f.decrypt(user.api_key_encrypted.encode()).decode()
        
        console.print(Panel(
            f"[bold blue]Decrypted API Key for {username}:[/bold blue]\n\n[bold yellow]{decrypted_key}[/bold yellow]",
            title="🔓 SECURE ACCESS",
            border_style="blue"
        ))
    except Exception as e:
        console.print(f"[red]Decryption Error: {e}[/red]")
    finally:
        db.close()

@app.command("delete")
def delete_key_cmd(username: str):
    """Revoke/Delete an API Key after verifying identity."""
    db: Session = SessionLocal()
    try:
        user = verify_admin_access(db, username)
        if not user: return
        
        if not user.api_key_encrypted:
            console.print(f"[yellow]User '{username}' already has no API Key.[/yellow]")
            return

        confirm = Prompt.ask(f"[bold red]Are you sure you want to REVOKE the API Key for {username}?[/bold red] (y/n)", default="n")
        if confirm.lower() == 'y':
            user.api_key_encrypted = None
            user.api_key_hashed = None
            db.commit()
            console.print(f"[bold green]✓ API Key for '{username}' has been revoked. The Mod will no longer be able to connect with it.[/bold green]")
        else:
            console.print("[yellow]Revocation cancelled.[/yellow]")
            
    finally:
        db.close()

if __name__ == "__main__":
    app()
