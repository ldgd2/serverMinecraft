import asyncio
import subprocess
import platform
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models.user import User
from routes.auth import get_current_user
from app.controllers.system_controller import SystemController
from app.controllers.system_controller import SystemController
from app.services.audit_service import AuditService
from database.schemas import SystemInfo
from core.responses import APIResponse

router = APIRouter(prefix="/system", tags=["System"])
system_controller = SystemController()

@router.get("/info", response_model=APIResponse[SystemInfo])
def get_system_info(current_user: User = Depends(get_current_user)):
    """Get system resources: CPU, RAM, Disk availability"""
    return APIResponse(status="success", message="System info retrieved", data=system_controller.get_system_info())

@router.get("/stats")
def get_system_stats(current_user: User = Depends(get_current_user)):
    """Get real-time system stats for monitoring dashboard"""
    return APIResponse(status="success", message="System stats retrieved", data=system_controller.get_system_stats())

@router.get("/service/status")
def get_service_status(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    return APIResponse(status="success", message="Service status retrieved", data=system_controller.get_service_status())

@router.post("/service/enable")
def enable_service(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    result = system_controller.enable_service()
    if not result["success"]:
        raise HTTPException(status_code=500, detail="Failed to enable service. Ensure admin privileges.")
    AuditService.log_action(db, current_user, "ENABLE_SERVICE", request.client.host, "Enabled system service")
    return APIResponse(status="success", message="Service enabled", data=result)

@router.post("/service/disable")
def disable_service(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    result = system_controller.disable_service()
    if not result["success"]:
        raise HTTPException(status_code=500, detail="Failed to disable service.")
    AuditService.log_action(db, current_user, "DISABLE_SERVICE", request.client.host, "Disabled system service")
    return APIResponse(status="success", message="Service disabled", data=result)

@router.post("/service/restart")
def restart_service(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    result = system_controller.restart_service()
    if not result["success"]:
        raise HTTPException(status_code=500, detail="Failed to restart service.")
    AuditService.log_action(db, current_user, "RESTART_SERVICE", request.client.host, "Restarted system service")
    return APIResponse(status="success", message="Service restart triggered", data=result)

@router.websocket("/service/logs")
async def service_logs_websocket(websocket: WebSocket):
    await websocket.accept()
    
    # Simple check for demo, in production use token
    # auth_header = websocket.headers.get("Authorization")
    
    
    process = None
    try:
        if platform.system().lower() == "linux":
            # Stream journalctl for the service
            service_name = system_controller.get_system_config().get("SERVICE_NAME", "minecraft-dashboard")
            cmd = ["sudo", "journalctl", "-u", service_name, "-n", "100", "-f"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
        else:
            # On windows, maybe stream the most recent log file if it exists
            # For now, just send a message
            await websocket.send_text("Log streaming only supported on Linux via journalctl currently.")
            await asyncio.sleep(2)
            await websocket.close()
            return

        if process and process.stdout:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                await websocket.send_text(line.decode().strip())
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try: await websocket.send_text(f"Error: {str(e)}")
        except: pass
    finally:
        if process:
            try: process.terminate()
            except: pass
        try: await websocket.close()
        except: pass

@router.get("/config")
def get_system_config(current_user: User = Depends(get_current_user)):
    """Read system configuration (.env)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    return APIResponse(status="success", message="System config retrieved", data=system_controller.get_system_config())

@router.post("/config")
def update_system_config(updates: dict, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update system configuration (.env)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin required")
    system_controller.update_system_config(updates)
    AuditService.log_action(db, current_user, "UPDATE_SYSTEM_CONFIG", request.client.host, "Updated system config")
    return APIResponse(status="success", message="System config updated", data=None)

