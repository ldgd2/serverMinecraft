import sys
import asyncio

# Enforce ProactorEventLoop on Windows for subprocess support (works with reload)
# Must be set before any other asyncio usage or import that might init loop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, Request, HTTPException
# StaticFiles and Templates removed for Pure API
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import Depends, APIRouter
from sqlalchemy.orm import Session
from database.connection import SessionLocal, get_db
from database.models.base import Base
from database.models.version import Version
from app.services.minecraft import server_service
from database.schemas import VersionResponse
from typing import List
from routes.auth import get_current_user
import uvicorn
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

class EnvFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.env'):
            from dotenv import load_dotenv
            load_dotenv(override=True)
            print("🔄 Reloaded .env file - SECRET_KEY updated dynamically")

# Router Imports
# Router Imports
from routes import auth, servers, system, files, mods, worlds, audit, versions, players, player_auth, bridge, backups
from app.routes.minecraft import router as minecraft_router

app = FastAPI(title="Minecraft Server Manager")

# CORS Configuration
allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins_str == "*":
    allow_origins = []
    allow_origin_regex = ".*"
else:
    allow_origins = [o.strip() for o in allowed_origins_str.split(",")]
    allow_origin_regex = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
os.makedirs("source/worlds", exist_ok=True)
os.makedirs("source/forge", exist_ok=True)
os.makedirs("source/fabric", exist_ok=True)
os.makedirs("source/paper", exist_ok=True)
os.makedirs("source/vanilla", exist_ok=True)
os.makedirs("servers", exist_ok=True)

# Pure API - No static mounts

# Custom Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if request.url.path.startswith("/api"):
        if isinstance(exc.detail, dict):
            # If it already has structure, return it directly or combine
            content = {"status": "error", "data": None}
            content.update(exc.detail)
            return JSONResponse(status_code=exc.status_code, content=content)
            
        return JSONResponse(
            status_code=exc.status_code,
            content={"status": "error", "message": str(exc.detail), "data": None}
        )
    return JSONResponse(status_code=exc.status_code, content={"status": "error", "message": str(exc.detail), "data": None})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(exc), "data": None}
        )
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

from fastapi.encoders import jsonable_encoder

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log the exact validation error to the console to help debug Flutter payload
    print(f"❌ VALIDATION ERROR ({request.url.path}): {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"status": "error", "message": "Validation Error", "data": exc.errors()})
    )

# Include API Routers in V1
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth.router)
api_v1_router.include_router(servers.router)
api_v1_router.include_router(system.router)
api_v1_router.include_router(files.router)
api_v1_router.include_router(mods.router)
api_v1_router.include_router(backups.router)
api_v1_router.include_router(worlds.router)
api_v1_router.include_router(audit.router)
api_v1_router.include_router(versions.router)
api_v1_router.include_router(players.router)
api_v1_router.include_router(player_auth.router)
api_v1_router.include_router(bridge.router)
api_v1_router.include_router(bridge.ws_router)

app.include_router(api_v1_router)
# Minecraft mod bridge - mounted directly (mod calls /api/minecraft/*, not /api/v1/...)
app.include_router(minecraft_router)

@app.on_event("startup")
async def startup_event():
    import sys
    import asyncio
    loop = asyncio.get_running_loop()
    print(f"DEBUG: Current Loop Type: {type(loop)}")
    print(f"DEBUG: Platform: {sys.platform}")
    
    # Verify WebSocket support
    try:
        import websockets
        print(f"[OK] WebSockets library available: {websockets.__version__}")
    except ImportError:
        print("[WARN] WARNING: WebSockets library not found - WebSocket endpoints may not work!")
    
    try:
        from uvicorn.protocols.websockets.websockets_impl import WebSocketProtocol
        print(f"[OK] Uvicorn WebSocket protocol loaded: {WebSocketProtocol.__name__}")
    except ImportError:
        print("[WARN] WARNING: Uvicorn WebSocket protocol not loaded - using fallback")
    
    # Print server addresses (Forced Flush for Windows support)
    import os
    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "8000")
    print_host = os.getenv("WS_HOST") or host
    print_port = os.getenv("WS_PORT") or port
    print(f"Starting Minecraft Server Manager on http://{host}:{port}", flush=True)
    print(f"WebSocket endpoints:", flush=True)
    print(f"  - Console: ws://{print_host}:{print_port}/api/v1/servers/{{name}}/console", flush=True)
    print(f"  - Status:  ws://{print_host}:{print_port}/api/v1/servers/{{name}}/status", flush=True)
    print(f"  - Chat:    ws://{print_host}:{print_port}/api/v1/servers/{{name}}/chat", flush=True)
    print(f"  - Downloads: ws://{print_host}:{print_port}/api/v1/versions/downloads/ws?token=YOUR_TOKEN", flush=True)
    
    # Auto-Migration for missing columns
    db = SessionLocal()
    try:
        from sqlalchemy import text
        print("Checking and fixing database schema...")
        queries = [
            "ALTER TABLE player_accounts ADD COLUMN IF NOT EXISTS total_player_kills INTEGER DEFAULT 0;",
            "ALTER TABLE player_accounts ADD COLUMN IF NOT EXISTS total_hostile_kills INTEGER DEFAULT 0;",
            "ALTER TABLE player_accounts ADD COLUMN IF NOT EXISTS total_genocide_score INTEGER DEFAULT 0;"
        ]
        for query in queries:
            db.execute(text(query))
        db.commit()
        print("Schema update complete.")
        
        server_service.load_servers_from_db(db)
    except Exception as e:
        print(f"Error updating schema or loading servers: {e}")
    finally:
        db.close()

# HTML Page views have been moved to routes/pages.py

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    # Start .env file watcher for dynamic SECRET_KEY reloading
    event_handler = EnvFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()

    try:
        # Force websockets implementation (cross-platform)
        uvicorn.run(
            app, 
            host=host, 
            port=port, 
            reload=False, 
            ws="websockets",
            log_level="info"
        )
    except KeyboardInterrupt:
        observer.stop()
        observer.join()
