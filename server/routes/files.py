from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from core.responses import APIResponse
from database.models import User
from routes.auth import get_current_user
from app.controllers.file_controller import FileController

router = APIRouter(prefix="/files", tags=["Files"])
file_controller = FileController()

@router.get("/{server_name}")
def list_files(server_name: str, path: str = ".", current_user: User = Depends(get_current_user)):
    try:
        files = file_controller.list_files(server_name, path)
        print(f"[OK] Listed files in {server_name}/{path}")
        return APIResponse(status="success", message="Files listed", data=files)
    except FileNotFoundError as e:
        print(f"[ERROR 404] {server_name} - {e}")
        raise HTTPException(status_code=404, detail="Server or path not found")
    except PermissionError as e:
        print(f"[ERROR 403] Path traversal detected in {server_name}/{path}")
        raise HTTPException(status_code=403, detail="Access denied - path traversal detected")

@router.post("/{server_name}/upload")
async def upload_file_endpoint(server_name: str, path: str = ".", file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    try:
        await file_controller.upload_file(server_name, path, file)
        print(f"[OK] Uploaded {file.filename} to {server_name}/{path}")
        return APIResponse(status="success", message="File uploaded and processed", data=None)
    except FileNotFoundError:
        print(f"[ERROR 404] Server not found: {server_name}")
        raise HTTPException(status_code=404, detail="Server not found")
    except PermissionError as e:
        print(f"[ERROR 403] Upload path traversal in {server_name}/{path}: {e}")
        raise HTTPException(status_code=403, detail="Access denied - invalid path")

@router.post("/{server_name}/config")
async def update_config(server_name: str, properties: dict, current_user: User = Depends(get_current_user)):
    try:
        await file_controller.update_config(server_name, properties)
        print(f"[OK] Config updated for {server_name}")
        return APIResponse(status="success", message="Config updated", data=None)
    except FileNotFoundError:
         print(f"[ERROR 404] Server not found: {server_name}")
         raise HTTPException(status_code=404, detail="Server not found")

@router.get("/{server_name}/content")
def get_file_content(server_name: str, path: str, current_user: User = Depends(get_current_user)):
    try:
        content = file_controller.get_content(server_name, path)
        print(f"[OK] Read file {server_name}/{path}")
        return APIResponse(status="success", message="File content retrieved", data={"content": content})
    except FileNotFoundError:
        print(f"[ERROR 404] File not found: {server_name}/{path}")
        raise HTTPException(status_code=404, detail="File not found")
    except ValueError as e:
        print(f"[ERROR 400] File error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

from pydantic import BaseModel
class FileSaveRequest(BaseModel):
    path: str
    content: str

@router.post("/{server_name}/save")
def save_file_content(server_name: str, data: FileSaveRequest, current_user: User = Depends(get_current_user)):
    try:
        file_controller.save_content(server_name, data.path, data.content)
        print(f"[OK] Saved file {server_name}/{data.path}")
        return APIResponse(status="success", message="File saved", data=None)
    except FileNotFoundError:
        print(f"[ERROR 404] File not found: {server_name}/{data.path}")
        raise HTTPException(status_code=404, detail="File not found")
    except PermissionError as e:
        print(f"[ERROR 403] Path traversal in save {server_name}/{data.path}: {e}")
        raise HTTPException(status_code=403, detail="Access denied - invalid path")

# ============================================
# GENERAL FILE BROWSER (Restricted Directories)
# ============================================
import os
from pathlib import Path

# Allowed root directories (relative to project root)
ALLOWED_ROOTS = {
    "servers": "servers",
    "worlds": "source/worlds",
    "versions": "source/versions",
}

def get_project_root():
    """Get the project root directory"""
    return Path(__file__).parent.parent.resolve()

def is_safe_path(base_path: Path, requested_path: Path) -> bool:
    """Check if requested path is within base path (prevent path traversal)"""
    try:
        requested_path.resolve().relative_to(base_path.resolve())
        return True
    except ValueError:
        return False

@router.get("/browse/roots")
def get_allowed_roots(current_user: User = Depends(get_current_user)):
    """Get list of allowed root directories"""
    project_root = get_project_root()
    roots = []
    
    print(f"[OK] Fetching allowed roots from {project_root}")
    for name, rel_path in ALLOWED_ROOTS.items():
        full_path = project_root / rel_path
        roots.append({
            "name": name.capitalize(),
            "path": name,
            "exists": full_path.exists(),
            "icon": "folder"
        })
        print(f"  - {name}: {full_path} (exists: {full_path.exists()})")
    
    return APIResponse(status="success", message="Roots retrieved", data=roots)

@router.get("/browse/{root_name}")
def browse_directory(
    root_name: str, 
    path: str = "",
    current_user: User = Depends(get_current_user)
):
    """Browse files in allowed directories"""
    if root_name not in ALLOWED_ROOTS:
        print(f"[ERROR 403] Invalid root directory: {root_name} (allowed: {list(ALLOWED_ROOTS.keys())})")
        raise HTTPException(status_code=403, detail=f"Directory not allowed. Allowed: {list(ALLOWED_ROOTS.keys())}")
    
    project_root = get_project_root()
    base_path = project_root / ALLOWED_ROOTS[root_name]
    
    # Handle path traversal
    if path:
        target_path = base_path / path
    else:
        target_path = base_path
    
    # Security check
    if not is_safe_path(base_path, target_path):
        print(f"[ERROR 403] Path traversal attempt: requested {target_path}, base {base_path}")
        raise HTTPException(status_code=403, detail="Access denied - path traversal detected")
    
    # Create directory if it doesn't exist (for empty roots)
    if not target_path.exists():
        target_path.mkdir(parents=True, exist_ok=True)
    
    if not target_path.is_dir():
        print(f"[ERROR 400] Not a directory: {target_path}")
        raise HTTPException(status_code=400, detail="Path is not a directory")
    
    items = []
    try:
        for item in target_path.iterdir():
            stat = item.stat()
            items.append({
                "name": item.name,
                "is_dir": item.is_dir(),
                "size": stat.st_size if item.is_file() else 0,
                "modified": stat.st_mtime,
                "extension": item.suffix.lower() if item.is_file() else None
            })
        
        # Sort: directories first, then files alphabetically
        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        print(f"[OK] Browsed {root_name}/{path} ({len(items)} items)")
        
    except PermissionError as e:
        print(f"[ERROR 403] Permission denied browsing {root_name}/{path}: {e}")
        raise HTTPException(status_code=403, detail="Access denied - permission error")
    
    return APIResponse(status="success", message="Directory browsed", data={
        "root": root_name,
        "current_path": path,
        "parent_path": str(Path(path).parent) if path else None,
        "items": items
    })

@router.get("/browse/{root_name}/content")
def get_file_content_general(
    root_name: str,
    path: str,
    current_user: User = Depends(get_current_user)
):
    """Get content of a text file"""
    if root_name not in ALLOWED_ROOTS:
        print(f"[ERROR 403] Invalid root: {root_name}")
        raise HTTPException(status_code=403, detail=f"Directory not allowed. Allowed: {list(ALLOWED_ROOTS.keys())}")
    
    project_root = get_project_root()
    base_path = project_root / ALLOWED_ROOTS[root_name]
    target_path = base_path / path
    
    # Security check
    if not is_safe_path(base_path, target_path):
        print(f"[ERROR 403] Path traversal in content read: {path}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not target_path.exists() or not target_path.is_file():
        print(f"[ERROR 404] File not found: {target_path}")
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check file size (max 5MB - increased)
    if target_path.stat().st_size > 5 * 1024 * 1024:
        print(f"[ERROR 400] File too large: {target_path}")
        raise HTTPException(status_code=400, detail="File too large to edit (max 5MB)")
    
    # Check if it's a binary file (Only restrict archives and media)
    # Allow .dat, .mca, .nbt, .conf, etc. to be opened as text
    restricted_extensions = {
        # Archives
        '.jar', '.zip', '.gz', '.tar', '.rar', '.7z', 
        # Media
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico',
        '.mp4', '.webm', '.avi', '.mkv', '.mp3', '.wav', '.ogg',
        # Executables
        '.exe', '.dll', '.so', '.dylib'
    }
    
    if target_path.suffix.lower() in restricted_extensions:
        print(f"[ERROR 400] Cannot edit binary file: {target_path}")
        raise HTTPException(status_code=400, detail="Cannot edit binary/media files")
    
    try:
        content = target_path.read_text(encoding='utf-8', errors='replace')
        print(f"[OK] Read file content: {target_path} ({len(content)} bytes)")
        return {
            "name": target_path.name,
            "path": path,
            "content": content,
            "size": target_path.stat().st_size
        }
    except Exception as e:
        print(f"[ERROR 500] Error reading file {target_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

class FileContentSave(BaseModel):
    path: str
    content: str

@router.post("/browse/{root_name}/save")
def save_file_content_general(
    root_name: str,
    data: FileContentSave,
    current_user: User = Depends(get_current_user)
):
    """Save content to a text file"""
    if root_name not in ALLOWED_ROOTS:
        print(f"[ERROR 403] Invalid root: {root_name}")
        raise HTTPException(status_code=403, detail=f"Directory not allowed. Allowed: {list(ALLOWED_ROOTS.keys())}")
    
    project_root = get_project_root()
    base_path = project_root / ALLOWED_ROOTS[root_name]
    target_path = base_path / data.path
    
    # Security check
    if not is_safe_path(base_path, target_path):
        print(f"[ERROR 403] Path traversal in save: {data.path}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if it's a restricted file
    restricted_extensions = {
        '.jar', '.zip', '.gz', '.tar', '.rar', '.7z', 
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico',
        '.mp4', '.webm', '.avi', '.mkv', '.mp3', '.wav', '.ogg',
        '.exe', '.dll', '.so', '.dylib'
    }
    
    if target_path.suffix.lower() in restricted_extensions:
        print(f"[ERROR 400] Cannot save binary file: {target_path}")
        raise HTTPException(status_code=400, detail="Cannot edit binary/media files")
    
    try:
        target_path.write_text(data.content, encoding='utf-8')
        print(f"[OK] Saved file: {target_path} ({len(data.content)} bytes)")
        return APIResponse(status="success", message="File saved successfully", data=None)
    except Exception as e:
        print(f"[ERROR 500] Error saving file {target_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

from fastapi.responses import FileResponse
import mimetypes

@router.get("/browse/{root_name}/media")
def get_media_file(
    root_name: str,
    path: str,
    current_user: User = Depends(get_current_user)
):
    """Serve media files (images, videos) directly"""
    if root_name not in ALLOWED_ROOTS:
        print(f"[ERROR 403] Invalid root: {root_name}")
        raise HTTPException(status_code=403, detail=f"Directory not allowed. Allowed: {list(ALLOWED_ROOTS.keys())}")
    
    project_root = get_project_root()
    base_path = project_root / ALLOWED_ROOTS[root_name]
    target_path = base_path / path
    
    # Security check
    if not is_safe_path(base_path, target_path):
        print(f"[ERROR 403] Path traversal in media: {path}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not target_path.exists() or not target_path.is_file():
        print(f"[ERROR 404] Media file not found: {target_path}")
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(str(target_path))
    if not mime_type:
        mime_type = 'application/octet-stream'
    
    print(f"[OK] Serving media: {target_path}")
    return FileResponse(
        path=str(target_path),
        media_type=mime_type,
        filename=target_path.name
    )


# ============================================
# FILE OPERATIONS (Copy, Move, Delete, etc.)
# ============================================
import shutil

class FileOperationRequest(BaseModel):
    source_path: str
    dest_path: str = None
    conflict: str = "fail" # fail, overwrite, rename

class CreateRequest(BaseModel):
    path: str
    type: str = "folder" # folder, file

class RenameRequest(BaseModel):
    path: str
    new_name: str

@router.post("/browse/{root_name}/upload")
async def upload_file_general(
    root_name: str,
    path: str = "",
    conflict: str = "fail",
    extract: bool = False,
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    if root_name not in ALLOWED_ROOTS:
        print(f"[ERROR 403] Invalid root for upload: {root_name}")
        raise HTTPException(status_code=403, detail=f"Directory not allowed. Allowed: {list(ALLOWED_ROOTS.keys())}")

    project_root = get_project_root()
    base_path = project_root / ALLOWED_ROOTS[root_name]
    target_dir = base_path / path

    if not is_safe_path(base_path, target_dir):
        print(f"[ERROR 403] Path traversal in upload: {path}")
        raise HTTPException(status_code=403, detail="Access denied")

    if not target_dir.exists():
         print(f"[ERROR 404] Upload target not found: {target_dir}")
         raise HTTPException(status_code=404, detail="Target directory not found")

    results = []
    
    for file in files:
        dest_path = target_dir / file.filename
        
        # Conflict resolution
        if dest_path.exists():
            if conflict == "fail":
                results.append({"name": file.filename, "status": "error", "message": "File exists"})
                continue
            elif conflict == "overwrite":
                pass # Will overwrite
            elif conflict == "rename":
                base, ext = os.path.splitext(file.filename)
                counter = 1
                while dest_path.exists():
                    dest_path = target_dir / f"{base} ({counter}){ext}"
                    counter += 1
        
        try:
            with open(dest_path, "wb") as f:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                
            if extract and file.filename.lower().endswith((".zip", ".7z")):
                 from app.services.file_service import file_service
                 file_service.extract_package(str(dest_path), str(target_dir))
                 print(f"[OK] Extracted {file.filename} to {target_dir}")

            print(f"[OK] Uploaded {file.filename} to {root_name}/{path}")
            results.append({"name": file.filename, "status": "success", "path": str(dest_path.relative_to(base_path))})
        except Exception as e:
            print(f"[ERROR] Upload failed for {file.filename}: {e}")
            results.append({"name": file.filename, "status": "error", "message": str(e)})
            
    return APIResponse(status="success", message="Files processed", data={"results": results})

@router.post("/browse/{root_name}/copy")
def copy_file_general(
    root_name: str,
    data: FileOperationRequest,
    current_user: User = Depends(get_current_user)
):
    if root_name not in ALLOWED_ROOTS:
        print(f"[ERROR 403] Invalid root for copy: {root_name}")
        raise HTTPException(status_code=403, detail=f"Directory not allowed. Allowed: {list(ALLOWED_ROOTS.keys())}")
    
    project_root = get_project_root()
    base_path = project_root / ALLOWED_ROOTS[root_name]
    
    source = base_path / data.source_path
    dest = base_path / data.dest_path
    
    if not is_safe_path(base_path, source) or not is_safe_path(base_path, dest):
        print(f"[ERROR 403] Path traversal in copy: {data.source_path} -> {data.dest_path}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not source.exists():
        print(f"[ERROR 404] Copy source not found: {source}")
        raise HTTPException(status_code=404, detail="Source not found")
        
    # Handle Conflict
    if dest.exists():
        if data.conflict == "fail":
             print(f"[ERROR 409] Copy destination exists: {dest}")
             raise HTTPException(status_code=409, detail="Destination exists")
        elif data.conflict == "overwrite":
            if dest.is_dir(): shutil.rmtree(dest)
            else: dest.unlink()
        elif data.conflict == "rename":
             base, ext = os.path.splitext(dest.name)
             counter = 1
             parent = dest.parent
             while dest.exists():
                 dest = parent / f"{base} ({counter}){ext}"
                 counter += 1

    try:
        if source.is_dir():
            shutil.copytree(source, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(source, dest)
        print(f"[OK] Copied {source} -> {dest}")
        return APIResponse(status="success", message="Copied successfully", data={"new_path": str(dest.relative_to(base_path))})
    except Exception as e:
        print(f"[ERROR 500] Copy failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/browse/{root_name}/move")
def move_file_general(
    root_name: str,
    data: FileOperationRequest,
    current_user: User = Depends(get_current_user)
):
    if root_name not in ALLOWED_ROOTS:
        print(f"[ERROR 403] Invalid root for move: {root_name}")
        raise HTTPException(status_code=403, detail=f"Directory not allowed. Allowed: {list(ALLOWED_ROOTS.keys())}")
    
    project_root = get_project_root()
    base_path = project_root / ALLOWED_ROOTS[root_name]
    
    source = base_path / data.source_path
    dest = base_path / data.dest_path
    
    if not is_safe_path(base_path, source) or not is_safe_path(base_path, dest):
        print(f"[ERROR 403] Path traversal in move: {data.source_path} -> {data.dest_path}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not source.exists():
        print(f"[ERROR 404] Move source not found: {source}")
        raise HTTPException(status_code=404, detail="Source not found")
        
    # Handle Conflict
    if dest.exists():
        if data.conflict == "fail":
             print(f"[ERROR 409] Move destination exists: {dest}")
             raise HTTPException(status_code=409, detail="Destination exists")
        elif data.conflict == "overwrite":
            if dest.is_dir(): shutil.rmtree(dest)
            else: dest.unlink()
        elif data.conflict == "rename":
             base, ext = os.path.splitext(dest.name)
             counter = 1
             parent = dest.parent
             while dest.exists():
                 dest = parent / f"{base} ({counter}){ext}"
                 counter += 1

    try:
        shutil.move(source, dest)
        print(f"[OK] Moved {source} -> {dest}")
        return APIResponse(status="success", message="Moved successfully", data={"new_path": str(dest.relative_to(base_path))})
    except Exception as e:
        print(f"[ERROR 500] Move failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.api_route("/browse/{root_name}/delete", methods=["DELETE", "POST"])
def delete_file_general(
    root_name: str,
    path: str,
    current_user: User = Depends(get_current_user)
):
    if root_name not in ALLOWED_ROOTS:
        print(f"[ERROR 403] Invalid root for delete: {root_name}")
        raise HTTPException(status_code=403, detail=f"Directory not allowed. Allowed: {list(ALLOWED_ROOTS.keys())}")
    
    project_root = get_project_root()
    base_path = project_root / ALLOWED_ROOTS[root_name]
    target = base_path / path
    
    if not is_safe_path(base_path, target):
        print(f"[ERROR 403] Path traversal in delete: {path}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not target.exists():
        print(f"[ERROR 404] Delete target not found: {target}")
        raise HTTPException(status_code=404, detail="Path not found")
        
    try:
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        print(f"[OK] Deleted {target}")
        return APIResponse(status="success", message="Deleted successfully", data=None)
    except Exception as e:
        print(f"[ERROR 500] Delete failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/browse/{root_name}/create")
def create_item_general(
    root_name: str,
    data: CreateRequest,
    current_user: User = Depends(get_current_user)
):
    if root_name not in ALLOWED_ROOTS:
        print(f"[ERROR 403] Invalid root for create: {root_name}")
        raise HTTPException(status_code=403, detail=f"Directory not allowed. Allowed: {list(ALLOWED_ROOTS.keys())}")
    
    project_root = get_project_root()
    base_path = project_root / ALLOWED_ROOTS[root_name]
    target = base_path / data.path
    
    if not is_safe_path(base_path, target):
        print(f"[ERROR 403] Path traversal in create: {data.path}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        if data.type == "folder":
            target.mkdir(parents=True, exist_ok=True)
        else:
            if not target.exists():
                target.touch()
        print(f"[OK] Created {data.type} at {target}")
        return APIResponse(status="success", message="Created successfully", data=None)
    except Exception as e:
        print(f"[ERROR 500] Create failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/browse/{root_name}/rename")
def rename_item_general(
    root_name: str,
    data: RenameRequest,
    current_user: User = Depends(get_current_user)
):
    if root_name not in ALLOWED_ROOTS:
        print(f"[ERROR 403] Invalid root for rename: {root_name}")
        raise HTTPException(status_code=403, detail=f"Directory not allowed. Allowed: {list(ALLOWED_ROOTS.keys())}")
    
    project_root = get_project_root()
    base_path = project_root / ALLOWED_ROOTS[root_name]
    
    source = base_path / data.path
    dest = source.parent / data.new_name
    
    if not is_safe_path(base_path, source) or not is_safe_path(base_path, dest):
        print(f"[ERROR 403] Path traversal in rename: {data.path} -> {data.new_name}")
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not source.exists():
        print(f"[ERROR 404] Rename source not found: {source}")
        raise HTTPException(status_code=404, detail="Source not found")
    
    if dest.exists():
        print(f"[ERROR 409] Rename destination exists: {dest}")
        raise HTTPException(status_code=409, detail="Name already taken")
        
    try:
        source.rename(dest)
        print(f"[OK] Renamed {source} -> {dest}")
        return APIResponse(status="success", message="Renamed successfully", data=None)
    except Exception as e:
        print(f"[ERROR 500] Rename failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/browse/{root_name}/extract")
def extract_archive_general(
    root_name: str,
    data: FileOperationRequest, # reusing source_path as archive, dest_path as extract_to
    current_user: User = Depends(get_current_user)
):
    if root_name not in ALLOWED_ROOTS:
        raise HTTPException(status_code=403, detail="Directory not allowed")
    
    project_root = get_project_root()
    base_path = project_root / ALLOWED_ROOTS[root_name]
    
    archive = base_path / data.source_path
    dest = base_path / (data.dest_path if data.dest_path else ".")
    
    if not is_safe_path(base_path, archive) or not is_safe_path(base_path, dest):
        raise HTTPException(status_code=403, detail="Access denied")
        
    if not archive.exists():
        raise HTTPException(status_code=404, detail="Archive not found")
        
    try:
        from app.services.file_service import file_service
        file_service.extract_package(str(archive), str(dest))
        return APIResponse(status="success", message="Extracted successfully", data=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
