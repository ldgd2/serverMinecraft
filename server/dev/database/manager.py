import typer
import sys
import os
import time

# Ensure parent is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from database.migrate import run_migrations, rollback_migration, reset_database, show_current, show_history, create_database
from database.seeder import run_all_seeders, run_specific_seeder
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

app = typer.Typer(help="Advanced Database Manager")
console = Console()

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        while True:
            console.clear()
            console.print(Panel.fit("[bold cyan]Database Manager[/bold cyan]", border_style="cyan"))
            console.print("[1] Migrate (Apply pending)")
            console.print("[2] Seeder (Populate dummy data)")
            console.print("[3] Initialize Database (First setup + Admin User)")
            console.print("[4] Reset Database (Wipe & Re-create)")
            console.print("[5] Manage PostgreSQL Roles (Users)")
            console.print("[0] Return to Main Menu")
            
            choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5", "0"], default="3")
            
            try:
                if choice == "1":
                    migrate_cmd()
                elif choice == "2":
                    seed_cmd(name="all")
                elif choice == "3":
                    init_db_cmd()
                elif choice == "4":
                    reset_cmd()
                elif choice == "5":
                    roles_cmd()
                elif choice == "0":
                    break
            except Exception as e:
                console.print(f"[bold red]An error occurred: {e}[/bold red]")
                
            Prompt.ask("\n[dim]Press Enter to continue...[/dim]")

@app.command("migrate")
def migrate_cmd():
    """Apply pending migrations"""
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("[cyan]Applying migrations...", total=None)
        success = run_migrations()
        time.sleep(1) # Visual effect
        
    if success:
        console.print("[bold green][OK] Migrations applied successfully.[/bold green]")
    else:
        console.print("[bold red][FAIL] Migrations failed.[/bold red]")

@app.command("seed")
def seed_cmd(name: str = typer.Argument("all")):
    """Run database seeders"""
    console.print(f"[bold blue]Running seeder: {name}[/bold blue]")
    if name == "all":
        run_all_seeders()
    else:
        run_specific_seeder(name)
    console.print("[bold green][OK] Seeding complete.[/bold green]")

@app.command("init-db")
def init_db_cmd():
    """Initialize database and create an admin user"""
    console.print(Panel("[bold yellow]PostgreSQL & App Database Initialization[/bold yellow]"))
    
    import os
    import secrets
    import string
    import importlib
    
    current_user = os.getenv("DB_USER", "postgres")
    
    console.print(f"Current database user in .env is: [cyan]{current_user}[/cyan]")
    choice = Prompt.ask("Do you want to [1] Keep this user or [2] Create a new dedicated admin user for the PostgreSQL DB?", choices=["1", "2"], default="1")
    
    if choice == "2":
        new_user = Prompt.ask("Enter new PostgreSQL admin username", default="mine_admin")
        
        # Password confirmation loop
        while True:
            pass1 = Prompt.ask(f"Enter password for PostgreSQL user '{new_user}'", password=True)
            pass2 = Prompt.ask("Repeat password", password=True)
            if pass1 == pass2:
                selected_password = pass1
                break
            else:
                console.print("[bold red]Passwords do not match! Please try again.[/bold red]")
        
        db_host = os.getenv("DB_HOST", "127.0.0.1")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "mine_db")
        
        console.print("[dim]Connecting to PostgreSQL as superuser to create the role and database...[/dim]")
        super_user = Prompt.ask("Enter superuser (e.g. postgres)", default="postgres")
        super_pass = Prompt.ask(f"Enter password for {super_user}", password=True)
        
        try:
            from dev.utils.database import bootstrap_postgres_db
            
            target_user, target_pass = bootstrap_postgres_db(
                host=db_host,
                port=db_port,
                db_name=db_name,
                super_user=super_user,
                super_pass=super_pass,
                target_user=new_user,
                target_password=selected_password
            )
            
            # We must reload env variables in this process so connection.py uses the new credentials
            os.environ["DB_USER"] = target_user
            os.environ["DB_PASSWORD"] = target_pass
            
            # Reload connection module so the SQLAlchemy Engine reconstructs the URL
            import database.connection
            importlib.reload(database.connection)
            
            console.print(f"[bold green][OK] PostgreSQL setup complete. Credentials saved to .env.[/bold green]")
            console.print(f"[bold green]User: {target_user} | Password: {target_pass}[/bold green]")
            
        except Exception as e:
            from dev.utils.core import safe_exception_str
            console.print(f"[bold red]PostgreSQL Error: {safe_exception_str(e)}[/bold red]")
            console.print("[yellow]Continuing with existing configuration...[/yellow]")
    
    
    with Progress(SpinnerColumn(), TextColumn("[cyan]Creating tables...[/cyan]"), console=console) as progress:
        task = progress.add_task("init", total=None)
        # Re-import create_database in case the module needs the new connection
        import database.migrate
        importlib.reload(database.migrate)
        from database.migrate import create_database as dynamic_create_database
        
        success = dynamic_create_database()
        time.sleep(1)
        
    if success:
        console.print("[bold green][OK] Database initialized.[/bold green]")
        
        console.print("\n[bold cyan]Create the Main Application Administrator Account (Minecraft Dashboard)[/bold cyan]")
        username = Prompt.ask("App Admin Username", default="admin")
        password = Prompt.ask("App Admin Password", password=True)
        
        from database.connection import SessionLocal
        from database.models.user import User
        from app.services.auth_service import get_password_hash
        
        db = SessionLocal()
        try:
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                console.print(f"[yellow]User {username} already exists.[/yellow]")
            else:
                user = User(
                    username=username,
                    hashed_password=get_password_hash(password),
                    is_admin=True,
                    is_active=True
                )
                db.add(user)
                db.commit()
                console.print("[bold green][OK] Administrator account created successfully![/bold green]")
        except Exception as e:
            console.print(f"[bold red]Error creating user: {e}[/bold red]")
            db.rollback()
        finally:
            db.close()
    else:
        console.print("[bold red][FAIL] Initialization failed.[/bold red]")

@app.command("reset")
def reset_cmd():
    """Reset database (Wipe all)"""
    confirm = Prompt.ask("[bold red]Are you sure you want to wipe the database?[/bold red] (yes/no)", default="no")
    if confirm.lower() == "yes":
        with Progress(SpinnerColumn(), TextColumn("[red]Resetting database...[/red]"), console=console) as progress:
            progress.add_task("reset", total=None)
            success = reset_database()
            time.sleep(1.5)
        
        if success:
            console.print("[bold green][OK] Database reset successfully.[/bold green]")
        else:
            console.print("[bold red][FAIL] Reset failed.[/bold red]")
    else:
        console.print("[yellow]Reset cancelled.[/yellow]")

@app.command("roles")
def roles_cmd():
    """Manage PostgreSQL database roles (users)"""
    console.print(Panel("[bold yellow]PostgreSQL Role Management[/bold yellow]"))
    
    import os
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_port = os.getenv("DB_PORT", "5432")
    
    super_user = Prompt.ask("Enter superuser (e.g. postgres)", default="postgres")
    super_pass = Prompt.ask(f"Enter password for {super_user}", password=True)
    
    try:
        import psycopg2
        from psycopg2 import sql
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        
        conn = psycopg2.connect(
            dbname="postgres", 
            user=super_user, 
            password=super_pass, 
            host=db_host, 
            port=db_port,
            connect_timeout=5,
            client_encoding='utf8'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        while True:
            console.print("\n[bold cyan]PostgreSQL Roles (Loggable):[/bold cyan]")
            cur.execute("SELECT rolname FROM pg_roles WHERE rolcanlogin = true ORDER BY rolname;")
            roles = [r[0] for r in cur.fetchall()]
            for r in roles:
                console.print(f" - {r}")
                
            console.print("\n[1] Create Role")
            console.print("[2] Change Password")
            console.print("[3] Delete Role")
            console.print("[0] Return")
            
            sub_choice = Prompt.ask("Action", choices=["1", "2", "3", "0"], default="0")
            
            if sub_choice == "1":
                new_role = Prompt.ask("New role name")
                while True:
                    p1 = Prompt.ask("Password", password=True)
                    p2 = Prompt.ask("Repeat password", password=True)
                    if p1 == p2:
                        cur.execute(sql.SQL("CREATE USER {} WITH PASSWORD {}").format(
                            sql.Identifier(new_role), sql.Literal(p1)
                        ))
                        console.print(f"[bold green]✔ Role '{new_role}' created successfully.[/bold green]")
                        break
                    else:
                        console.print("[bold red]Passwords do not match! Please try again.[/bold red]")
            
            elif sub_choice == "2":
                role_to_edit = Prompt.ask("Role to change password", choices=roles)
                while True:
                    p1 = Prompt.ask("New password", password=True)
                    p2 = Prompt.ask("Repeat password", password=True)
                    if p1 == p2:
                        cur.execute(sql.SQL("ALTER USER {} WITH PASSWORD {}").format(
                            sql.Identifier(role_to_edit), sql.Literal(p1)
                        ))
                        console.print(f"[bold green]✔ Password updated for '{role_to_edit}'.[/bold green]")
                        break
                    else:
                        console.print("[bold red]Passwords do not match! Please try again.[/bold red]")
            
            elif sub_choice == "3":
                role_to_del = Prompt.ask("Role to delete", choices=roles)
                if role_to_del == super_user:
                    console.print("[bold red]Cannot delete the superuser you are currently using![/bold red]")
                    continue
                confirm = Prompt.ask(f"Are you sure you want to delete role '{role_to_del}'? (y/n)", default="n")
                if confirm.lower() == 'y':
                    cur.execute(sql.SQL("DROP USER {}").format(sql.Identifier(role_to_del)))
                    console.print(f"[bold green]✔ Role '{role_to_del}' deleted.[/bold green]")
            
            elif sub_choice == "0":
                break
                
        cur.close()
        conn.close()
        
    except Exception as e:
        from dev.utils.core import safe_exception_str
        console.print(f"[bold red]Error: {safe_exception_str(e)}[/bold red]")
