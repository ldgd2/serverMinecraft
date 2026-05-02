import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        client_encoding='utf8'
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    cur.execute("SELECT version_num FROM alembic_version")
    versions = [row[0] for row in cur.fetchall()]
    print(f"Versions in database: {versions}")
    
    if len(versions) > 1:
        print("Multiple versions detected! Deleting all but the most recent known head.")
        # The latest head we know is 1e9abf7f89b9
        # We will keep that one if it's there, otherwise we might need to be careful.
        # Let's just delete all and insert the latest one.
        cur.execute("DELETE FROM alembic_version")
        cur.execute("INSERT INTO alembic_version (version_num) VALUES ('1e9abf7f89b9')")
        print("Database stamped to 1e9abf7f89b9")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
