import sys
import io
# Fix Unicode encoding on Windows (PowerShell uses charmap by default)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import asyncio
import uvicorn
import os

# 1. Enforce ProactorEventLoop on Windows BEFORE ANYTHING ELSE
# This is required for asyncio.create_subprocess_exec to work on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if __name__ == "__main__":
    # 2. Verify websockets library is available
    try:
        import websockets
        print(f"[OK] WebSockets library loaded: {websockets.__version__}")
    except ImportError as e:
        print(f"[ERROR] WebSockets library not available: {e}")
        print("Please run: pip install websockets")
        sys.exit(1)
    
    # 3. Run Uvicorn with explicit WebSocket configuration
    # Pass the app object directly to avoid import issues and subprocess spawning
    from main import app
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Define host and port for Uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    # Address printing moved to main.py startup_event
    
    # Use WebSocket implementation from .env
    ws_impl = os.getenv("WS_IMPLEMENTATION", "websockets")
    print(f"Using WebSocket implementation: {ws_impl}")
    
    uvicorn.run(
        app, 
        host=host, 
        port=port, 
        reload=False, 
        ws=ws_impl,
        log_level="info"
    )
