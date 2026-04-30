import os
import secrets
import string
from dev.utils.core import update_env_variable

def bootstrap_postgres_db(host, port, db_name, super_user, super_pass, target_user=None, target_password=None):
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    """
    Connects to PostgreSQL as superuser, creates a new role and database if they don't exist.
    Returns (new_user, new_password)
    """
    # Force client encoding in environment for psycopg2
    os.environ["PGCLIENTENCODING"] = "UTF8"
    
    if not target_user:
        target_user = "mine_admin"
        
    if not target_password:
        alphabet = string.ascii_letters + string.digits
        target_password = ''.join(secrets.choice(alphabet) for _ in range(16))
    
    try:
        # Use a very short timeout for bootstrapping
        conn = psycopg2.connect(
            dbname="postgres", 
            user=super_user, 
            password=super_pass, 
            host=host, 
            port=port,
            client_encoding='utf8',
            connect_timeout=5
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Create user if not exists
        cur.execute(sql.SQL("SELECT 1 FROM pg_roles WHERE rolname={}").format(sql.Literal(target_user)))
        if not cur.fetchone():
            cur.execute(sql.SQL("CREATE USER {} WITH PASSWORD {}").format(
                sql.Identifier(target_user),
                sql.Literal(target_password)
            ))
        
        # Create database if not exists
        cur.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname={}").format(sql.Literal(db_name)))
        if not cur.fetchone():
            cur.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(
                sql.Identifier(db_name),
                sql.Identifier(target_user)
            ))
        else:
            # Ensure privileges
            cur.execute(sql.SQL("ALTER DATABASE {} OWNER TO {}").format(
                sql.Identifier(db_name),
                sql.Identifier(target_user)
            ))
            cur.execute(sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                sql.Identifier(db_name),
                sql.Identifier(target_user)
            ))
            
        cur.close()
        conn.close()
        
        # Save to .env immediately
        update_env_variable("DB_HOST", host)
        update_env_variable("DB_PORT", str(port))
        update_env_variable("DB_NAME", db_name)
        update_env_variable("DB_USER", target_user)
        update_env_variable("DB_PASSWORD", target_password)
        update_env_variable("DB_ENGINE", "postgresql")
        
        return target_user, target_password
        
    except Exception as e:
        # Extreme safety for UnicodeDecodeError on Windows Spanish locales
        msg = ""
        try:
            msg = str(e)
        except UnicodeDecodeError:
            try:
                # If it's a psycopg2 Error, the message might be in bytes in args
                if hasattr(e, 'args') and len(e.args) > 0:
                    raw_msg = e.args[0]
                    if isinstance(raw_msg, bytes):
                        msg = raw_msg.decode('cp1252', errors='replace')
                    else:
                        msg = repr(raw_msg)
                else:
                    msg = repr(e)
            except:
                msg = "PostgreSQL connection failed (Encoding error in server message)"
        
        if not msg:
            msg = "Unknown PostgreSQL connection error"
            
        raise Exception(msg)

def bootstrap_postgres_db_sudo(db_name, target_user, target_password, host="127.0.0.1", port=5432):
    """
    Uses system 'psql' via 'sudo -u postgres' to bootstrap.
    Ideal for Linux servers where the user is root.
    """
    import subprocess
    import sys
    
    # Helper to run psql commands
    def run_psql(cmd):
        res = subprocess.run(['sudo', '-u', 'postgres', 'psql', '-c', cmd], capture_output=True, text=True)
        return res.returncode == 0, res.stderr

    # 1. Create user (Ignore error if already exists)
    run_psql(f"CREATE USER {target_user} WITH PASSWORD '{target_password}';")
    
    # 2. Create database
    success, err = run_psql(f"CREATE DATABASE {db_name} OWNER {target_user};")
    if not success and "already exists" not in err:
        # If it failed for other reasons, try to just grant permissions
        pass

    # 3. Grant privileges
    run_psql(f"ALTER DATABASE {db_name} OWNER TO {target_user};")
    run_psql(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {target_user};")

    # Save to .env immediately
    update_env_variable("DB_HOST", host)
    update_env_variable("DB_PORT", str(port))
    update_env_variable("DB_NAME", db_name)
    update_env_variable("DB_USER", target_user)
    update_env_variable("DB_PASSWORD", target_password)
    update_env_variable("DB_ENGINE", "postgresql")
    
    return target_user, target_password
