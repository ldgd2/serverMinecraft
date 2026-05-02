import psycopg2
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
db = os.getenv('DB_NAME')

try:
    # Try with a DSN string
    dsn = f"host={host} port={port} dbname={db} user={user} password={password}"
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT version_num FROM alembic_version")
    versions = [row[0] for row in cur.fetchall()]
    print(f"Versions: {versions}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error with DSN: {e}")
    
try:
    # Try with keyword arguments
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=db,
        user=user,
        password=password
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT version_num FROM alembic_version")
    versions = [row[0] for row in cur.fetchall()]
    print(f"Versions (kwargs): {versions}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error with kwargs: {e}")
