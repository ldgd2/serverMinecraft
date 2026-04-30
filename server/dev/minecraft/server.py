import typer
import uvicorn
import os
from dev.utils.core import print_header

app = typer.Typer(help="Server management commands")

@app.command("run")
def run_server(
    host: str = typer.Option("0.0.0.0", help="Host to bind"),
    port: int = typer.Option(8000, help="Port to bind"),
    reload: bool = typer.Option(True, help="Enable auto-reload (Dev mode)"),
    prod: bool = typer.Option(False, "--prod", help="Production mode (disables reload, changes logging)")
):
    """
    Start the Minecraft Manager Web Server
    """
    if prod:
        reload = False
        print_header("Starting Server in PRODUCTION mode")
    else:
        print_header("Starting Server in DEVELOPMENT mode")

    # Ensure required directories exist before start
    os.makedirs("logs", exist_ok=True)
    
    # We use websockets library explicitly as per previous fixes
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        ws="websockets",
        log_level="info"
    )

@app.command("prod")
def run_prod():
    """Shortcut for production run"""
    run_server(host="0.0.0.0", port=80, reload=False, prod=True)
