from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import uuid
import jwt
from database.connection import get_db, SessionLocal
from database.models.user import User
from database.models.version import Version
from routes.auth import get_current_user
from app.services.version_service import VersionService
from pydantic import BaseModel
from core.responses import APIResponse
import os

router = APIRouter(prefix="/versions", tags=["Versions"])

# In-memory download state: { task_id: { status: 'pending'|'downloading'|'completed'|'error', progress: 0, details: str } }
active_downloads: Dict[str, Dict] = {}

def verify_ws_token(token: str) -> Optional[User]:
    """Verify JWT token and return user. Used for WebSocket authentication."""
    try:
        SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret")
        ALGORITHM = os.getenv("ALGORITHM", "HS256")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            return None
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            return user
        finally:
            db.close()
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

class VersionDownloadRequest(BaseModel):
    loader_type: str
    mc_version: str
    loader_version_id: Optional[str] = "latest"

def task_download_version(task_id: str, request: VersionDownloadRequest):
    db = SessionLocal()
    try:
        service = VersionService(db)
        
        def update_progress(percent, current, total, speed=0, eta=0):
            active_downloads[task_id]["progress"] = percent
            active_downloads[task_id]["current_bytes"] = current
            active_downloads[task_id]["total_bytes"] = total
            active_downloads[task_id]["speed_bps"] = speed
            active_downloads[task_id]["eta_seconds"] = eta
            active_downloads[task_id]["details"] = f"{current}/{total} bytes ({speed/1024:.1f} KB/s, ETA: {int(eta)}s)"

        active_downloads[task_id]["status"] = "downloading"
        
        service.download_version(
            request.loader_type, 
            request.mc_version, 
            request.loader_version_id, 
            progress_callback=update_progress
        )
        
        active_downloads[task_id]["status"] = "completed"
        active_downloads[task_id]["progress"] = 100
        
    except Exception as e:
        active_downloads[task_id]["status"] = "error"
        active_downloads[task_id]["error"] = str(e)
    finally:
        db.close()

@router.get("/") 
def list_installed_versions(grouped: bool = False, db: Session = Depends(get_db)):
    service = VersionService(db)
    versions = service.get_installed_versions()
    
    if not grouped:
        mapped = [{
            "id": v.id,
            "name": v.name,
            "loader_type": v.loader_type,
            "mc_version": v.mc_version,
            "loader_version": v.loader_version,
            "file_size": v.file_size,
            "downloaded": v.downloaded,
            "local_path": v.local_path
        } for v in versions]
        return APIResponse(status="success", message="Installed versions retrieved", data=mapped)
    else:
        grouped_dct = {}
        for v in versions:
            loader = v.loader_type.upper()
            if loader not in grouped_dct:
                grouped_dct[loader] = []
            grouped_dct[loader].append({
                "id": v.id,
                "name": v.name,
                "mc_version": v.mc_version,
                "loader_version": v.loader_version,
                "file_size": v.file_size,
                "downloaded": v.downloaded,
                "local_path": v.local_path
            })
        return APIResponse(status="success", message="Grouped installed versions retrieved", data=grouped_dct)

@router.get("/stats")
def get_version_stats(db: Session = Depends(get_db)):
    service = VersionService(db)
    return APIResponse(status="success", message="Version stats retrieved", data=service.get_version_stats())

@router.get("/remote/{loader_type}")
def list_remote_versions(loader_type: str, db: Session = Depends(get_db)):
    service = VersionService(db)
    return APIResponse(status="success", message="Remote versions retrieved", data=service.get_remote_versions(loader_type))

@router.post("/download")
def download_version(
    request: VersionDownloadRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verificar si ya está descargado
    existing = db.query(Version).filter(
        Version.loader_type == request.loader_type.upper(),
        Version.mc_version == request.mc_version
    ).first()
    
    if existing and existing.downloaded:
         raise HTTPException(status_code=400, detail="Esta versión ya se encuentra descargada e instalada.")

    task_id = str(uuid.uuid4())
    active_downloads[task_id] = {
        "status": "pending",
        "progress": 0,
        "loader": request.loader_type,
        "version": request.mc_version
    }
    
    background_tasks.add_task(task_download_version, task_id, request)
    return APIResponse(status="success", message="Download started", data={"task_id": task_id})

@router.get("/downloads/active")
def get_active_downloads(current_user: User = Depends(get_current_user)):
    return APIResponse(status="success", message="Active downloads retrieved", data=active_downloads)

@router.post("/downloads/{task_id}/ack")
def acknowledge_download(task_id: str, current_user: User = Depends(get_current_user)):
    if task_id in active_downloads:
        del active_downloads[task_id]
    return APIResponse(status="success", message="Download acknowledged", data=None)

@router.websocket("/downloads/ws")
async def websocket_downloads(websocket: WebSocket):
    print(f"[WS CONNECT] Downloads endpoint from {websocket.client}")
    token = websocket.query_params.get("token")
    if not token:
        auth_header = websocket.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    if not token:
        await websocket.close(code=1008, reason="No authentication token")
        return
    
    user = verify_ws_token(token)
    if not user:
        await websocket.close(code=1008, reason="Invalid or expired token")
        return
    
    await websocket.accept()
    import asyncio
    message_count = 0
    last_state = None
    was_active = False
    try:
        while True:
            message_count += 1
            updates = active_downloads.copy()
            all_finished = True
            for task_id, info in updates.items():
                if info.get("status") in ["pending", "downloading"]:
                    all_finished = False
                    was_active = True
                    break
            
            if updates != last_state:
                if updates:
                    print(f"[WS SEND] Downloads update (msg #{message_count}): {len(updates)} tasks")
                await websocket.send_json(updates)
                last_state = updates.copy()
            
            if was_active and all_finished:
                print(f"[WS DISCONNECT] Todas las descargas terminaron. Cerrando socket.")
                break
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        print(f"[WS DISCONNECT] Downloads connection closed for {user.username} (sent {message_count} updates)")
    except Exception as e:
        print(f"[WS ERROR] Downloads error for {user.username}: {e}")
