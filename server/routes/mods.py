from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from database.connection import get_db
from database.models.user import User
from routes.auth import get_current_user
from app.services.mod_service import mod_service
from app.services.minecraft import server_service
from core.responses import APIResponse

router = APIRouter(prefix="/servers/{server_name}/mods", tags=["Mods"])

@router.get("/")
@router.get("/")
async def list_mods(server_name: str, loader: str = None, current_user: User = Depends(get_current_user)):
    # Verify server exists
    if not server_service.get_process(server_name) and not os.path.exists(os.path.join(server_service.base_dir, server_name)):
         # Check DB if process not active? For now assume valid if folder exists or service knows it
         pass
         
    return APIResponse(status="success", message="Mods retrieved", data=await mod_service.get_installed_mods(server_name, loader))

@router.post("/upload")
async def upload_mod(
    server_name: str, 
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user)
):
    try:
        if not file.filename.endswith(('.jar', '.zip', '.rar')):
            raise HTTPException(status_code=400, detail="Only .jar, .zip, and .rar files are allowed")
            
        result = await mod_service.upload_mod(server_name, file)
        return APIResponse(status="success", message="Mod uploaded", data=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_mods(payload: dict, current_user: User = Depends(get_current_user)):
    # payload: { query: str, version: str, loader: str }
    query = payload.get("query")
    version = payload.get("version")
    loader = payload.get("loader")
    
    if not query or not version:
         raise HTTPException(status_code=400, detail="Missing query or version")
         
    return APIResponse(status="success", message="Mods searched", data=await mod_service.search_mods(query, version, loader))

@router.post("/install")
async def install_mod_endpoint(server_name: str, payload: dict, current_user: User = Depends(get_current_user)):
    # payload: { project_id: str, version: str, loader: str }
    project_id = payload.get("project_id")
    version = payload.get("version")
    loader = payload.get("loader")
    
    # Get server to verify existence
    # ...
    
    try:
        await mod_service.install_mod(server_name, project_id, version, loader)
        return APIResponse(status="success", message="Mod installed successfully", data=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/")
async def delete_multiple_mods(server_name: str, payload: dict, current_user: User = Depends(get_current_user)):
    # payload: { files: [str], loader: str }
    files = payload.get("files", [])
    loader = payload.get("loader")
    
    results = []
    for f in files:
        success = await mod_service.delete_mod(server_name, f, loader)
        results.append({"filename": f, "success": success})
        
    return APIResponse(status="success", message="Multiple mods deleted", data=results)

@router.delete("/{filename}")
async def delete_mod(server_name: str, filename: str, loader: str = None, current_user: User = Depends(get_current_user)):
    success = await mod_service.delete_mod(server_name, filename, loader)
    if not success:
        raise HTTPException(status_code=404, detail="Mod not found")
    return APIResponse(status="success", message="Mod deleted", data=None)

@router.put("/rename")
async def rename_mod(server_name: str, payload: dict, current_user: User = Depends(get_current_user)):
    # payload: { old_name: str, new_name: str }
    old_name = payload.get("old_name")
    new_name = payload.get("new_name")
    
    if not old_name or not new_name:
        raise HTTPException(status_code=400, detail="Missing old_name or new_name")
        
    success = await mod_service.rename_mod(server_name, old_name, new_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to rename mod")
        
    return APIResponse(status="success", message="Mod renamed successfully", data=None)

import os
