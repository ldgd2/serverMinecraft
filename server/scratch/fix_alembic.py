import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.connection import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    result = db.execute(text("SELECT version_num FROM alembic_version"))
    versions = [row[0] for row in result]
    print(f"Versions in database: {versions}")
    
    if len(versions) > 1:
        print("Multiple versions detected! Cleaning up...")
        # Keep only the one that is the latest in history
        # Based on my history check, the latest is 1e9abf7f89b9
        # But we should be careful.
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
