import typer
import shutil
import os
import datetime
from dev.utils.core import print_header, print_success, print_error, print_info

app = typer.Typer(help="Backup utilities")

@app.command("create")
def create_backup(name: str = typer.Option(None, help="Custom name for the backup")):
    """Create a zip backup of critical files (database, env, config)"""
    print_header("Creating Backup")
    
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = name if name else f"backup_{timestamp}"
    backup_path = os.path.join(backup_dir, backup_name)
    
    # Files/Dirs to include
    include_paths = [
        "database/instance",  # SQLite DBs
        ".env",
        "config",             # If exists
        "requirements.txt"
    ]
    
    # Create a temp folder to collect files
    temp_dir = os.path.join(backup_dir, f"temp_{timestamp}")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        files_copied = 0
        for path in include_paths:
            if os.path.exists(path):
                dest = os.path.join(temp_dir, os.path.basename(path))
                if os.path.isdir(path):
                    shutil.copytree(path, dest)
                else:
                    shutil.copy2(path, dest)
                files_copied += 1
        
        if files_copied == 0:
            print_error("No files found to backup!")
            shutil.rmtree(temp_dir)
            return

        # Zip it
        shutil.make_archive(backup_path, 'zip', temp_dir)
        print_success(f"Backup created at: {backup_path}.zip")
        
    except Exception as e:
        print_error(f"Backup failed: {e}")
    finally:
        # Cleanup temp
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@app.command("list")
def list_backups():
    """List available backups"""
    print_header("Available Backups")
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        print_info("No backups directory found.")
        return
        
    files = [f for f in os.listdir(backup_dir) if f.endswith(".zip")]
    for f in files:
        size = os.path.getsize(os.path.join(backup_dir, f)) / (1024*1024)
        print_info(f"{f} ({size:.2f} MB)")
