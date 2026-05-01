from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List
import os

from routes.auth import get_current_user
from database.models.user import User
from app.services.backup_service import BackupService
from core.responses import APIResponse

router = APIRouter(prefix="/api/v1/backups", tags=["Database Backups"])
backup_service = BackupService()

@router.get("/", response_model=List[dict])
def list_backups(current_user: User = Depends(get_current_user)):
    """List all available database backups."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can manage backups")
    return backup_service.list_backups()

@router.post("/create")
def create_backup(current_user: User = Depends(get_current_user)):
    """Trigger a new full system backup (DB + Files)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can manage backups")
    
    try:
        filename = backup_service.create_full_backup()
        return APIResponse.success(
            message="Full backup created successfully",
            data={"filename": filename}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{filename}")
def download_backup(filename: str, current_user: User = Depends(get_current_user)):
    """Download a specific backup file."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can manage backups")
    
    file_path = os.path.join(backup_service.backup_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Backup file not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@router.post("/restore/{filename}")
def restore_backup(filename: str, current_user: User = Depends(get_current_user)):
    """Restore the full system (DB + Files) from a backup file."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can manage backups")
    
    try:
        success = backup_service.restore_full_backup(filename)
        if success:
            return APIResponse.success(message="System restored successfully. You may need to restart your servers.")
        else:
            return APIResponse.error(message="Restore failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{filename}")
def delete_backup(filename: str, current_user: User = Depends(get_current_user)):
    """Delete a backup file."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can manage backups")
    
    if backup_service.delete_backup(filename):
        return APIResponse.success(message="Backup deleted")
    else:
        raise HTTPException(status_code=404, detail="Backup not found")
