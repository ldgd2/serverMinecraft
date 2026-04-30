import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database.connection")

def get_connection_url():
    """
    Synthesizes the database URL based on environment variables.
    Handles the directory creation for SQLite.
    """
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
        
    engine_type = os.getenv("DB_ENGINE", "postgresql").lower()

    if engine_type == "sqlite":
        # SQLite: Handle file pathing and directory scaffolding
        db_name = os.getenv("DB_NAME", "minecraft_manager.db")
        
        # Logic to find the absolute path to /database/instance
        # This file is in /project/database/connection.py
        # We want /project/database/instance/
        current_dir = os.path.dirname(os.path.abspath(__file__))
        instance_dir = os.path.join(current_dir, "instance")
        
        # Create directory if it doesn't exist (Active Scaffolding)
        if not os.path.exists(instance_dir):
            try:
                os.makedirs(instance_dir, exist_ok=True)
                logger.info(f"Created SQLite instance directory: {instance_dir}")
            except OSError as e:
                logger.error(f"Could not create database directory: {e}")
                raise

        db_path = os.path.join(instance_dir, db_name)
        
        # Return SQLite URL (Absolute path)
        # Using 3 slashes for absolute path on Windows/Linux correctly handled by python
        return f"sqlite:///{db_path}"

    else:
        # RDBMS: Construct URL generically
        driver_map = {
            'postgresql': 'postgresql+psycopg2',
            'mysql': 'mysql+pymysql',
        }
        driver = driver_map.get(engine_type, engine_type)
        
        return URL.create(
            drivername=driver,
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT")) if os.getenv("DB_PORT") else None,
            database=os.getenv("DB_NAME")
        )

def create_app_engine():
    """
    Configures the SQLAlchemy Engine with dialect-specific options.
    """
    url = get_connection_url()
    # Need to check engine type again to set kwargs
    str_url = str(url)
    is_sqlite = str_url.startswith("sqlite")
    is_mysql = "mysql" in str_url
    is_postgres = "postgres" in str_url
    
    # Base arguments
    kwargs = {
        'echo': os.getenv("DB_ECHO", "False").lower() == 'true',
        'future': True
    }
    
    if is_sqlite:
        # Allow multi-threaded access with better timeout
        kwargs['connect_args'] = {
            'check_same_thread': False, 
            'timeout': 30  # Increased from 60 to 30 for faster failure
        }
    
    elif is_mysql:
        # Handle connection timeouts
        kwargs['pool_recycle'] = 3600
        kwargs['pool_pre_ping'] = True
        kwargs['pool_size'] = int(os.getenv("DB_POOL_SIZE", 5))
        kwargs['max_overflow'] = int(os.getenv("DB_MAX_OVERFLOW", 10))

    elif is_postgres:
        # Ultra-High Performance PostgreSQL Settings
        kwargs['pool_pre_ping'] = True
        kwargs['pool_size'] = int(os.getenv("DB_POOL_SIZE", 50))
        kwargs['max_overflow'] = int(os.getenv("DB_MAX_OVERFLOW", 100))
        kwargs['pool_recycle'] = 1800  # Recycle connections every 30 mins
        kwargs['pool_timeout'] = 30
        kwargs['isolation_level'] = "READ COMMITTED"
        
        # Optimize execution performance
        kwargs['use_insertmanyvalues'] = True
        kwargs['connect_args'] = {
            "application_name": "minecraft_server_manager",
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
            "options": "-c client_encoding=utf8"
        }

    engine = create_engine(url, **kwargs)

    # Enable WAL mode for SQLite for better concurrency
    if is_sqlite:
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=30000")  # 30 seconds in milliseconds
            cursor.close()

    return engine

# Internal storage for the engine and session factory
_engine = None
_SessionLocal = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_app_engine()
    return _engine

def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

def SessionLocal():
    """Compatibility wrapper for existing code calling SessionLocal()"""
    factory = get_session_factory()
    return factory()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
