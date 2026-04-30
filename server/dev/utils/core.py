import typer
import os
import re
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

# Custom theme for the CLI
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "error": "bold red",
    "success": "bold green",
    "header": "bold white on blue",
})

# Imports for create_user_service
from database.connection import SessionLocal
from database.models.user import User
from app.services.auth_service import get_password_hash, verify_password
import time
from sqlalchemy.exc import OperationalError

console = Console(theme=custom_theme)

def print_header(text: str):
    """Prints a styled header panel."""
    console.print(Panel(f"[bold white]{text}[/bold white]", style="blue", expand=False))

def print_success(text: str):
    """Prints a success message."""
    console.print(f"[success]✔ {text}[/success]")

def print_error(text: str):
    """Prints an error message."""
    console.print(f"[error]✖ {text}[/error]")

def print_info(text: str):
    """Prints an info message."""
    console.print(f"[info]ℹ {text}[/info]")

def print_warning(text: str):
    """Prints a warning message."""
    console.print(f"[warning]⚠ {text}[/warning]")

def update_env_variable(key: str, value: str):
    """
    Updates or adds a key-value pair in the .env file.
    Preserves existing comments and structure.
    """
    env_path = os.path.join(os.getcwd(), ".env")
    
    if not os.path.exists(env_path):
        # Create if not exists
        with open(env_path, "w") as f:
            f.write(f"{key}={value}\n")
        return

    with open(env_path, "r") as f:
        content = f.read()

    # Regex to find the key
    # Matches "KEY=value" or "KEY = value"
    pattern = re.compile(rf"^{key}\s*=\s*.*$", re.MULTILINE)
    
    if pattern.search(content):
        # Replace existing
        new_content = pattern.sub(f"{key}={value}", content)
    else:
        # Append to end
        if content and not content.endswith("\n"):
            content += "\n"
        new_content = content + f"{key}={value}\n"
        
    with open(env_path, "w") as f:
        f.write(new_content)
    
    
    print_success(f"Updated .env: {key}={value}")

def create_user_service(username, password):
    db = SessionLocal()
    max_retries = 3
    retry_delay = 1

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return False, f"User '{username}' already exists."
        
        # Hash password
        hashed_password = get_password_hash(password)
        
        # Create user
        new_user = User(username=username, hashed_password=hashed_password, is_admin=True)
        db.add(new_user)
        
        # Retry loop for commit
        for attempt in range(max_retries):
            try:
                db.commit()
                break
            except OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    raise e
        
        # Verify immediately
        db.refresh(new_user)
        if not verify_password(password, new_user.hashed_password):
             # This should theoretically never happen if hashing works, but good for sanity check
             return True, f"User '{username}' created, BUT immediate password verification FAILED. Please report this."

        return True, f"User '{username}' created successfully."
        
    except Exception as e:
        db.rollback()
        return False, f"Error creating user: {safe_exception_str(e)}"
    finally:
        db.close()

def safe_exception_str(e: Exception) -> str:
    """
    Extracts a human-readable string from an exception, handling potential
    UnicodeDecodeErrors on Windows (e.g. Spanish characters in PostgreSQL errors).
    """
    try:
        return str(e)
    except (UnicodeDecodeError, Exception):
        try:
            if hasattr(e, 'args') and len(e.args) > 0:
                raw_msg = e.args[0]
                if isinstance(raw_msg, bytes):
                    # Try system default (likely cp1252 on Spanish Windows)
                    return raw_msg.decode('cp1252', errors='replace')
                return repr(raw_msg)
            return repr(e)
        except:
            return "An unexpected error occurred (Encoding failure in message)"
