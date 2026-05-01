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

app = typer.Typer(help="Security & API Key Management")
console = Console()

def get_fernet():
    """Genera un objeto Fernet basado en el SECRET_KEY del sistema."""
    secret = os.getenv("SECRET_KEY", "default-secret-change-me-for-security")
    # Fernet requiere una clave de 32 bytes en base64
    key = hashlib.sha256(secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))

@app.command()
def generate_key(username: str = typer.Argument(..., help="Administrator username")):
    """Generate a secure API Key for a specific administrator."""
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username, User.is_admin == True).first()
        if not user:
            console.print(f"[red]Error: User '{username}' not found or is not an administrator.[/red]")
            return

        # Generar nueva llave segura
        raw_key = secrets.token_urlsafe(32)
        
        # Encriptar (para lectura)
        f = get_fernet()
        encrypted_key = f.encrypt(raw_key.encode()).decode()
        
        # Hash (para validación rápida)
        hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()
        
        user.api_key_encrypted = encrypted_key
        user.api_key_hashed = hashed_key
        db.commit()

        console.print(Panel(
            f"[bold green]API Key generated for {username}:[/bold green]\n\n[yellow]{raw_key}[/yellow]\n\n"
            "[dim]Save this key now. It will be encrypted in the database.[/dim]",
            title="🔑 New API Key",
            border_style="green"
        ))
    finally:
        db.close()

@app.command()
def list_keys():
    """List all administrators who have an API Key generated."""
    db: Session = SessionLocal()
    try:
        users = db.query(User).filter(User.api_key_encrypted != None).all()
        
        if not users:
            console.print("[yellow]No users found with active API Keys.[/yellow]")
            return

        table = Table(title="Administrators with API Keys", border_style="cyan")
        table.add_column("ID", style="dim")
        table.add_column("Username", style="bold green")
        table.add_column("Status", style="magenta")

        for u in users:
            table.add_row(str(u.id), u.username, "Encrypted & Safe")

        console.print(table)
    finally:
        db.close()

@app.command()
def show_key(username: str = typer.Argument(..., help="Username to view the key for")):
    """View an existing API Key (requires admin password verification)."""
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not user.api_key_encrypted:
            console.print(f"[red]Error: No API Key found for user '{username}'.[/red]")
            return

        # Pedir contraseña para validar
        password = Prompt.ask(f"[bold cyan]Enter password for {username} to decrypt key[/bold cyan]", password=True)
        
        if not verify_password(password, user.hashed_password):
            console.print("[red]❌ Authentication failed: Incorrect password.[/red]")
            return

        # Desencriptar
        try:
            f = get_fernet()
            decrypted_key = f.decrypt(user.api_key_encrypted.encode()).decode()
            
            console.print(Panel(
                f"[bold green]Decrypted API Key for {username}:[/bold green]\n\n[yellow]{decrypted_key}[/yellow]",
                title="🔓 Secure Decryption",
                border_style="blue"
            ))
        except Exception as e:
            console.print(f"[red]Error decrypting key: {e}[/red]")
            
    finally:
        db.close()
