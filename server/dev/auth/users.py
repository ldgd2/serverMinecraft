import typer
from rich.console import Console
from rich.prompt import Prompt
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import SessionLocal
from database.models.user import User
from app.services.auth_service import get_password_hash
from dev.utils.core import print_header, print_success, print_error, create_user_service

app = typer.Typer(help="User management commands")
console = Console()

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    Interactive User Seeder
    """
    if ctx.invoked_subcommand is not None:
        return
        
    print_header("Interactive User Management")
    
    while True:
        username = Prompt.ask("[bold cyan]Enter username[/bold cyan]")
        
        while True:
            password = Prompt.ask("[bold cyan]Enter password[/bold cyan]", password=True)
            password_confirm = Prompt.ask("[bold cyan]Repeat password[/bold cyan]", password=True)
            
            if password == password_confirm:
                break
            else:
                console.print("[bold red]Passwords do not match! Please try again.[/bold red]")
        
        console.print(f"\n[yellow]Creating user: {username}[/yellow]")
        
        success, message = create_user_service(username, password)
        
        if success:
            print_success(message)
        else:
            print_error(message)
            
        if not Prompt.ask("\n[bold]Create another user?[/bold]", choices=["y", "n"], default="n") == "y":
            break
            
    Prompt.ask("\n[dim]Press Enter to return to Main Menu...[/dim]")

if __name__ == "__main__":
    app()
