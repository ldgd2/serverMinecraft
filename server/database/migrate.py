"""
Migration Runner
Main entry point for running database migrations using Alembic
"""
import sys
import os
import subprocess

# Add the project root to the Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)



def create_database():
    """Create database tables if they don't exist and stamp alembic head"""
    print("=" * 50)
    print("Initializing Database...")
    print("=" * 50)
    
    try:
        # Import here to avoid early loading issues
        from database.connection import get_engine
        from database.models import Base 
        # Make sure all models are imported so Base knows about them
        from database.models.user import User
        from database.models.server import Server
        from database.models.version import Version
        from database.models.bitacora import Bitacora
        
        print(f"[INIT] Creating tables via SQLAlchemy...")
        Base.metadata.create_all(bind=get_engine())
        print(f"[INIT] Tables created successfully.")
        
        print(f"[INIT] Stamping Alembic header...")
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "stamp", "head"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout)
            print("\n[INIT] Database initialized and stamped successfully ✓")
        else:
            print(f"[INIT] Stamping failed ✗")
            err = result.stderr or result.stdout
            if "Multiple heads" in err or "Multiple head revisions" in err:
                print("[INIT] Detected multiple heads in DB. Attempting forced clean...")
                try:
                    conn = get_engine().connect()
                    from sqlalchemy import text
                    conn.execute(text("DELETE FROM alembic_version"))
                    # Re-try stamping
                    subprocess.run([sys.executable, "-m", "alembic", "stamp", "heads"], cwd=PROJECT_ROOT)
                    conn.commit()
                    print("[INIT] Forced clean successful.")
                except Exception as ex:
                    print(f"[INIT] Forced clean failed: {ex}")
            else:
                print(err)
            return False
            
    except Exception as e:
        from dev.utils.core import safe_exception_str
        print(f"[INIT] Error initializing database: {safe_exception_str(e)}")
        return False
        
    return True


def run_migrations():
    """Run all pending migrations"""
    print("=" * 50)
    print("Running Database Migrations...")
    print("=" * 50)
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout)
            print("\n[MIGRATE] Migrations completed successfully ✓")
        else:
            print(f"[MIGRATE] Migration failed ✗")
            err = (result.stderr or "") + (result.stdout or "")
            if "Multiple head" in err or "Multiple heads" in err:
                print("[MIGRATE] Detected multiple heads in DB. Attempting forced clean...")
                try:
                    from database.connection import get_engine
                    from sqlalchemy import text
                    with get_engine().connect() as conn:
                        conn.execute(text("DELETE FROM alembic_version"))
                        conn.commit()
                    # After cleaning, we must stamp to a valid head
                    subprocess.run([sys.executable, "-m", "alembic", "stamp", "heads"], cwd=PROJECT_ROOT)
                    print("[MIGRATE] Forced clean successful. Please try again.")
                except Exception as ex:
                    print(f"[MIGRATE] Forced clean failed: {ex}")
            else:
                print(err)
            return False
    except Exception as e:
        print(f"[MIGRATE] Error running migrations: {e}")
        return False
    
    return True


def rollback_migration():
    """Rollback the last migration"""
    print("Rolling back last migration...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "downgrade", "-1"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout)
            print("\n[MIGRATE] Rollback completed successfully ✓")
        else:
            print(f"[MIGRATE] Rollback failed ✗")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"[MIGRATE] Error rolling back: {e}")
        return False
    
    return True


def reset_database():
    """Reset database by rolling back all migrations and re-running them"""
    print("=" * 50)
    print("Resetting Database...")
    print("=" * 50)
    
    try:
        # Downgrade to base
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "downgrade", "base"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"[MIGRATE] Reset downgrade failed ✗")
            print(result.stderr)
            return False
        
        # Upgrade to head
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout)
            print("\n[MIGRATE] Database reset completed successfully ✓")
        else:
            print(f"[MIGRATE] Reset upgrade failed ✗")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"[MIGRATE] Error resetting database: {e}")
        return False
    
    return True


def show_current():
    """Show current migration status"""
    print("Current migration status:")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "current"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except Exception as e:
        print(f"Error checking status: {e}")


def show_history():
    """Show migration history"""
    print("Migration history:")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "history"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    except Exception as e:
        print(f"Error checking history: {e}")


def print_help():
    """Print help message"""
    print("""
Database Migration Tool
=======================

Usage: python database/migrate.py [command]

Commands:
  run       Run all pending migrations (default)
  rollback  Rollback the last migration
  reset     Reset database (rollback all, then migrate)
  status    Show current migration status
  history   Show migration history
  help      Show this help message

Examples:
  python database/migrate.py          # Run migrations
  python database/migrate.py run      # Run migrations  
  python database/migrate.py rollback # Rollback last migration
  python database/migrate.py reset    # Reset and re-migrate
""")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "run"
    
    commands = {
        "run": run_migrations,
        "rollback": rollback_migration,
        "reset": reset_database,
        "status": show_current,
        "history": show_history,
        "help": print_help,
    }
    
    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print_help()
