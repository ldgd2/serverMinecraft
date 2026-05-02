import os
from dotenv import load_dotenv

load_dotenv()

vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
for v in vars:
    val = os.getenv(v)
    if val:
        print(f"{v}: {val} (Hex: {val.encode('utf-8', errors='replace').hex()})")
    else:
        print(f"{v}: None")
