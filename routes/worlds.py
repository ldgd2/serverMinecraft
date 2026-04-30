from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from database.connection import get_db
from database.models.world import World, ServerWorld
from database.models.server import Server
from database.models.user import User
from database.models.bitacora import Bitacora
from routes.auth import get_current_user
from database.schemas import WorldCreate, WorldResponse, WorldAssignRequest
import os
import shutil
import zipfile
import datetime
import nbtlib
from core.responses import APIResponse

router = APIRouter(prefix="/worlds", tags=["Worlds"])

WORLDS_DIR = "source/worlds"

# Ensure worlds directory exists
os.makedirs(WORLDS_DIR, exist_ok=True)

def extract_world_metadata(world_path: str) -> dict:
    metadata = {
        "LevelName": None,
        "RandomSeed": None,
        "DataVersion": None
    }
    
    level_dat_path = os.path.join(world_path, "level.dat")
    
    # Try to find level.dat in immediate subdirectories if not in root
    if not os.path.exists(level_dat_path):
        for item in os.listdir(world_path):
            sub_path = os.path.join(world_path, item)
            if os.path.isdir(sub_path):
                potential_dat = os.path.join(sub_path, "level.dat")
                if os.path.exists(potential_dat):
                    level_dat_path = potential_dat
                    break
    
    if os.path.exists(level_dat_path):
        try:
            nbt_file = nbtlib.load(level_dat_path)
            # data is usually in 'Data' tag
            if 'Data' in nbt_file:
                data = nbt_file['Data']
                
                if 'LevelName' in data:
                    metadata["LevelName"] = str(data['LevelName'])
                
                if 'RandomSeed' in data:
                    metadata["RandomSeed"] = str(data['RandomSeed'])
                
                if 'DataVersion' in data:
                     metadata["DataVersion"] = str(data['DataVersion'])
            elif nbt_file.root and 'Data' in nbt_file.root:
                 # Alternative structure depending on nbtlib version/file structure
                 data = nbt_file.root['Data']
                 if 'LevelName' in data: metadata["LevelName"] = str(data['LevelName'])
                 if 'RandomSeed' in data: metadata["RandomSeed"] = str(data['RandomSeed'])
                 if 'DataVersion' in data: metadata["DataVersion"] = str(data['DataVersion'])

        except Exception as e:
            print(f"Error reading level.dat: {e}")
            
    return metadata

@router.get("/", response_model=APIResponse[List[WorldResponse]])
def list_worlds(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return APIResponse(status="success", message="Worlds listed", data=db.query(World).order_by(World.name).all())


@router.post("/", response_model=APIResponse[WorldResponse])
async def create_world(
    name: str = Form(...),
    seed: Optional[str] = Form(None),
    original_version: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Create world directory
    world_path = os.path.join(WORLDS_DIR, name)
    os.makedirs(world_path, exist_ok=True)
    
    # Save uploaded ZIP
    zip_path = os.path.join(world_path, "world.zip")
    with open(zip_path, "wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    
    # Extract ZIP
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(world_path)
    
    # Extract Metadata
    metadata = extract_world_metadata(world_path)
    
    # Update fields if auto-detected and not provided (or to override/supplement)
    # Strategy: Use extracted metadata to fill in blanks or clarify 'Parsed' data
    # The requirement says: 
    # "If name (from form) is generic or empty, use extracted name." -> logic below
    # "Update seed and original_version fields with extracted data."
    
    final_name = name
    if metadata["LevelName"] and (not name or name.lower() in ["world", "new world", "default"]):
        final_name = metadata["LevelName"]
        # Rename directory if we change the name? 
        # Requirement doesn't explicitly say to rename the directory on disk, but it's cleaner.
        # But 'world_path' relies on 'name'. 
        # Let's keep directory as 'name' to avoid complexity of moving files for now, unless 'name' was really empty.
        # But 'name' is required in Form(...).
        pass

    final_seed = seed
    if metadata["RandomSeed"]:
        final_seed = metadata["RandomSeed"]
        
    final_version = original_version
    if metadata["DataVersion"]:
        final_version = metadata["DataVersion"]

    # Calculate size
    total_size = sum(
        os.path.getsize(os.path.join(dirpath, filename))
        for dirpath, _, filenames in os.walk(world_path)
        for filename in filenames
    )
    size_mb = total_size // (1024 * 1024)
    
    # Create DB entry
    world = World(
        name=final_name,
        seed=final_seed,
        original_version=final_version,
        last_used_version=final_version,
        local_path=world_path,
        size_mb=size_mb
    )
    db.add(world)
    db.commit()
    db.refresh(world)
    
    # Log action
    log = Bitacora(
        username=current_user.username,
        action="WORLD_UPLOAD",
        details=f"Uploaded world: {name}"
    )
    db.add(log)
    db.commit()
    
    return APIResponse(status="success", message="World created successfully", data=world)


@router.get("/{world_id}", response_model=APIResponse[WorldResponse])
def get_world(world_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    world = db.query(World).filter(World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return APIResponse(status="success", message="World retrieved", data=world)


@router.delete("/{world_id}")
def delete_world(world_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    world = db.query(World).filter(World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    # Delete files
    if world.local_path and os.path.exists(world.local_path):
        shutil.rmtree(world.local_path)
    
    # Delete junction entries
    db.query(ServerWorld).filter(ServerWorld.world_id == world_id).delete()
    
    # Delete world
    db.delete(world)
    db.commit()
    
    # Log action
    log = Bitacora(
        username=current_user.username,
        action="WORLD_DELETE",
        details=f"Deleted world: {world.name}"
    )
    db.add(log)
    db.commit()
    
    return APIResponse(status="success", message="World deleted", data=None)


@router.post("/{world_id}/assign")
def assign_world_to_servers(
    world_id: int,
    request: WorldAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    world = db.query(World).filter(World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    copied_servers = []
    
    for server_id in request.server_ids:
        server = db.query(Server).filter(Server.id == server_id).first()
        if not server:
            continue
        
        # Copy world files to server directory
        server_world_path = os.path.join("servers", server.name, "world")
        if world.local_path and os.path.exists(world.local_path):
            if os.path.exists(server_world_path):
                shutil.rmtree(server_world_path)
            shutil.copytree(world.local_path, server_world_path)
        
        # Create junction entry
        existing = db.query(ServerWorld).filter(
            ServerWorld.server_id == server_id,
            ServerWorld.world_id == world_id
        ).first()
        
        if not existing:
            junction = ServerWorld(
                server_id=server_id,
                world_id=world_id,
                copied_at=datetime.datetime.utcnow()
            )
            db.add(junction)
        
        copied_servers.append(server.name)
    
    db.commit()
    
    # Log action
    log = Bitacora(
        username=current_user.username,
        action="WORLD_ASSIGN",
        details=f"Assigned world '{world.name}' to servers: {', '.join(copied_servers)}"
    )
    db.add(log)
    db.commit()
    
    return APIResponse(status="success", message=f"World copied to {len(copied_servers)} servers", data=None)


@router.get("/{world_id}/servers")
def get_world_servers(world_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get list of servers this world is assigned to"""
    junctions = db.query(ServerWorld).filter(ServerWorld.world_id == world_id).all()
    server_ids = [j.server_id for j in junctions]
    servers = db.query(Server).filter(Server.id.in_(server_ids)).all()
    return APIResponse(status="success", message="Servers retrieved", data=[{"id": s.id, "name": s.name, "status": s.status} for s in servers])
