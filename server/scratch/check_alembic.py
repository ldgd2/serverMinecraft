from sqlalchemy import text, create_engine
import os
from dotenv import load_dotenv

load_dotenv()

user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
db = os.getenv('DB_NAME')

engine_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
engine = create_engine(engine_url)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        versions = [row[0] for row in result]
        print(f"Versions in database: {versions}")
except Exception as e:
    print(f"Error: {e}")
