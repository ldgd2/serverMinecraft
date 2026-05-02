import psycopg2
import os

try:
    # Hardcoded for test
    conn = psycopg2.connect("host=127.0.0.1 port=5432 dbname=mine_db user=postgres password=postgres")
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT version_num FROM alembic_version")
    versions = [row[0] for row in cur.fetchall()]
    print(f"Versions: {versions}")
    if len(versions) > 1:
        print("Cleaning up versions...")
        cur.execute("DELETE FROM alembic_version")
        cur.execute("INSERT INTO alembic_version (version_num) VALUES ('1e9abf7f89b9')")
        print("Done.")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
