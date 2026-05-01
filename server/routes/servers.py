import asyncio
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, File, UploadFile, Request, BackgroundTasks
from fastapi.responses import FileResponse

from sqlalchemy.orm import Session
from typing import List, Dict
from database.connection import get_db
from app.controllers.server_controller import ServerController
from app.controllers.file_controller import FileController
from app.services.audit_service import AuditService
from database.schemas import ServerCreate, ServerUpdate, ServerResponse, ServerStats, ModSearchConnect, ServerCommandRequest, BanRequest, UpdateBanRequest, ChatRequest, EventRequest, CinematicRequest, ParanoiaRequest, SpecialEventRequest
from database.models.user import User
from database.models.server import Server
from routes.auth import get_current_user
from core.responses import APIResponse

router = APIRouter(prefix="/servers", tags=["Servers"])
server_controller = ServerController()
file_controller = FileController()

active_creations: Dict[str, Dict] = {}

class GlobalStatusManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_update(self, data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                pass

global_status_manager = GlobalStatusManager()

def task_create_server(task_id: str, server_id: int, host: str):
    # Create a new session for the background task
    from database.connection import SessionLocal
    from database.models.server import Server
    db = SessionLocal()
    try:
        def update_progress(percent: int, details: str):
            active_creations[task_id]["progress"] = percent
            active_creations[task_id]["details"] = details

        active_creations[task_id]["status"] = "creating"
        
        # Get server data from DB
        db_server = db.query(Server).filter(Server.id == server_id).first()
        if not db_server:
            raise Exception("Server record not found")

        # Call service to do the actual file work
        # We might need a modified service method or just use the current one if it handles existing records
        from app.services.minecraft.service import server_service
        
        # NOTE: The service's create_server normally creates the DB record.
        # We will wrap it or handle the logic here.
        # Actually, let's just use the controller but we need to ensure it doesn't duplicate.
        # For now, let's assume we call a 'setup_existing_server' or similar.
        # To avoid massive refactor of service, let's just run the logic manually here or update service.
        
        server = server_controller.setup_server_files(
            db, 
            db_server,
            progress_callback=update_progress
        )
        
        active_creations[task_id]["status"] = "completed"
        active_creations[task_id]["progress"] = 100
        active_creations[task_id]["details"] = "Server created successfully"
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        active_creations[task_id]["status"] = "error"
        active_creations[task_id]["error"] = str(e)
        # Update server status to ERROR in DB
        try:
            db_server = db.query(Server).filter(Server.id == server_id).first()
            if db_server:
                db_server.status = "ERROR"
                db.commit()
        except: pass
    finally:
        db.close()



@router.get("/")
def list_servers(grouped: bool = False, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    servers = server_controller.get_all_servers(db)
    from database.schemas import ServerResponse
    
    if not grouped:
        mapped = [ServerResponse.from_orm(s).dict() for s in servers]
        return APIResponse(status="success", message="Servers listed", data=mapped)
    else:
        grouped_dct = {}
        for s in servers:
            loader = s.mod_loader.upper() if s.mod_loader else "VANILLA"
            if loader not in grouped_dct:
                grouped_dct[loader] = []
            grouped_dct[loader].append(ServerResponse.from_orm(s).dict())
            
        return APIResponse(status="success", message="Grouped servers listed", data=grouped_dct)

@router.post("/", response_model=APIResponse[dict])
def create_server(
    server_data: ServerCreate, 
    request: Request, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Create DB Record synchronously first
    try:
        # Check if exists
        existing = db.query(Server).filter(Server.name == server_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Server with this name already exists")
            
        new_server = Server(
            name=server_data.name,
            version=server_data.version,
            ram_mb=server_data.ram_mb,
            port=server_data.port,
            online_mode=server_data.online_mode,
            motd=server_data.motd,
            mod_loader=server_data.mod_loader,
            cpu_cores=server_data.cpu_cores,
            disk_mb=server_data.disk_mb,
            max_players=server_data.max_players,
            status="CREATING"
        )
        db.add(new_server)
        db.commit()
        db.refresh(new_server)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    import uuid
    task_id = str(uuid.uuid4())
    active_creations[task_id] = {
        "status": "pending",
        "progress": 0,
        "details": "Initializing creation...",
        "name": server_data.name
    }
    
    background_tasks.add_task(task_create_server, task_id, new_server.id, request.client.host)
    
    # Audit sync BEFORE background starts is fine
    AuditService.log_action(db, current_user, "CREATE_SERVER_START", request.client.host, f"Started creating server {server_data.name}")
    
    from database.schemas import ServerResponse
    return APIResponse(
        status="success", 
        message="Server creation started", 
        data=ServerResponse.from_orm(new_server).dict()
    )

@router.get("/creations/active")
def get_active_creations(current_user: User = Depends(get_current_user)):
    """Get status of active server creations"""
    return APIResponse(status="success", message="Active creations retrieved", data=active_creations)

@router.post("/creations/{task_id}/ack")
def acknowledge_creation(task_id: str, current_user: User = Depends(get_current_user)):
    """Remove task from tracking"""
    if task_id in active_creations:
        del active_creations[task_id]
    return APIResponse(status="success", message="Creation acknowledged", data=None)



@router.patch("/{name}", response_model=APIResponse[ServerResponse])
def update_server(name: str, server_data: ServerUpdate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = server_data.dict(exclude_unset=True)
    server = server_controller.update_server(db, name, data)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    AuditService.log_action(db, current_user, "UPDATE_SERVER", request.client.host, f"Updated server {name} with {data}")
    return APIResponse(status="success", message="Server updated", data=server)

@router.delete("/{name}")
def delete_server(name: str, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    server_controller.delete_server(db, name)
    AuditService.log_action(db, current_user, "DELETE_SERVER", request.client.host, f"Deleted server {name}")
    return APIResponse(status="success", message="Server deleted", data=None)

@router.post("/{name}/control/{action}")
async def control_server(name: str, action: str, request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if action == "restart":
        background_tasks.add_task(server_controller.restart_server, name)
        res = True
    elif action == "start":
        res = await server_controller.start_server(name)
    elif action == "stop":
        res = await server_controller.stop_server(name)
    elif action == "kill":
        res = server_controller.kill_server(name)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    if not res:
         raise HTTPException(status_code=404, detail="Server not found or operation failed")
    
    AuditService.log_action(db, current_user, f"{action.upper()}_SERVER", request.client.host, f"Action {action} on {name}")
    return APIResponse(status="success", message=f"Action {action} started" if action == "restart" else f"Action {action} executed", data=None)

@router.get("/{name}/stats", response_model=APIResponse[ServerStats])
def get_server_stats(name: str, current_user: User = Depends(get_current_user)):
    return APIResponse(status="success", message="Stats requested", data=server_controller.get_server_stats(name))

@router.get("/{name}/config")
async def get_server_config(name: str, current_user: User = Depends(get_current_user)):
    """Get server.properties as JSON dictionary"""
    try:
        data = await file_controller.get_config(name)
        return APIResponse(status="success", message="Config retrieved", data=data)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Server or config file not found")
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.post("/{name}/config")
async def update_server_config(name: str, properties: dict, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update server.properties using JSON dictionary"""
    try:
        await file_controller.update_config(name, properties)
        AuditService.log_action(db, current_user, "UPDATE_CONFIG", request.client.host, f"Updated config for {name}")
        return APIResponse(status="success", message="Config updated", data=None)
    except FileNotFoundError:
         raise HTTPException(status_code=404, detail="Server not found")
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@router.post("/{name}/command")
async def send_command(name: str, command: ServerCommandRequest, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    cmd_text = command.command
    if cmd_text:
        await server_controller.send_command(name, cmd_text)
        AuditService.log_action(db, current_user, "SEND_COMMAND", request.client.host, f"Sent command to {name}: {cmd_text}")
    return APIResponse(status="success", message="Command sent", data=None)

@router.websocket("/{name}/console")
async def websocket_endpoint(websocket: WebSocket, name: str):
    print(f"[WS CONNECT] Console endpoint for server: {name}")
    await websocket.accept()
    print(f"[WS ACCEPTED] Console connection established for: {name}")
    queue = server_controller.get_console_queue(name)
    
    if not queue:
        print(f"[WS ERROR] Server not found: {name}")
        await websocket.close(code=4004, reason="Server not found")
        return
    
    try:
        # 1. Send recent history from file (tail)
        import os
        log_file = os.path.join("servers", name, "logs", "latest.log")
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                    # Read last 100 lines
                    f.seek(0, os.SEEK_END)
                    pos = f.tell()
                    lines_found = 0
                    buffer = ""
                    chunk_size = 1024
                    
                    while pos > 0 and lines_found <= 100:
                        pos = max(0, pos - chunk_size)
                        f.seek(pos)
                        chunk = f.read(chunk_size)
                        lines_found += chunk.count('\n')
                        buffer = chunk + buffer
                    
                    # Take last 100
                    recent_lines = buffer.split('\n')[-100:]
                    for line in recent_lines:
                        if line.strip():
                            await websocket.send_text(line.strip())
            except Exception as e:
                print(f"[WS ERROR] History read error: {e}")

        # 2. Stream new logs
        message_count = 0
        while True:
            log_line = await queue.get()
            message_count += 1
            await websocket.send_text(log_line)
    except WebSocketDisconnect:
        print(f"[WS DISCONNECT] Console connection closed for: {name}")
    except Exception as e:
        print(f"[WS ERROR] Console error for {name}: {e}")

@router.websocket("/{name}/status")
async def websocket_status(websocket: WebSocket, name: str):
    print(f"[WS CONNECT] Status endpoint for server: {name}")
    await websocket.accept()
    print(f"[WS ACCEPTED] Status connection established for: {name}")
    import asyncio
    from app.services.minecraft import server_service
    process = server_service.get_process(name)
    
    if not process:
        print(f"[WS ERROR] Server process not found: {name}")
        await websocket.close(code=4004, reason="Server not found")
        return
        
    last_sent = {}
    status_count = 0
    try:
        while True:
             stats = server_controller.get_server_stats(name)
             players = process.get_online_players()
             current_state = {
                  "stats": stats,
                  "players": players,
                  "count": len(players)
             }
             
             needs_send = False
             if not last_sent:
                  needs_send = True
             else:
                  last_ram = last_sent.get("stats", {}).get("ram_usage_mb", 0)
                  curr_ram = stats.get("ram_usage_mb", 0)
                  last_cpu = last_sent.get("stats", {}).get("cpu_usage_percent", 0)
                  curr_cpu = stats.get("cpu_usage_percent", 0)
                  
                  if abs(curr_ram - last_ram) > 20 or abs(curr_cpu - last_cpu) > 3:
                       needs_send = True
                  elif last_sent.get("players") != players:
                       needs_send = True
                        
             if needs_send:
                  status_count += 1
                  print(f"[WS SEND] Status {name} (msg #{status_count}): RAM={stats.get('ram_usage_mb')}MB, CPU={stats.get('cpu_usage_percent')}%, Players={len(players)}")
                  await websocket.send_json(current_state)
                  last_sent = current_state
                  
             await asyncio.sleep(2)
    except WebSocketDisconnect:
        print(f"[WS DISCONNECT] Status connection closed for: {name} (sent {status_count} updates)")
    except Exception as e:
        print(f"[WS ERROR] Status error for {name}: {e}")

@router.websocket("/ws/status-updates")
async def global_status_ws(websocket: WebSocket):
    await global_status_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep alive
    except WebSocketDisconnect:
        global_status_manager.disconnect(websocket)

async def broadcast_server_updates():
    """Background task to broadcast server status/stats changes to all connected clients"""
    from database.connection import SessionLocal
    from database.models.server import Server
    # Use the global server_controller instance defined at the top
    
    last_states = {}
    
    while True:
        try:
            db = SessionLocal()
            servers = db.query(Server).all()
            
            updates = []
            for s in servers:
                # Get current runtime data
                server_controller._inject_runtime_data(s)
                
                current = {
                    "status": s.status,
                    "cpu": s.cpu_usage,
                    "ram": s.ram_usage,
                    "players": s.current_players,
                    "disk": s.disk_usage
                }
                
                # Compare with last state
                if s.name not in last_states or last_states[s.name] != current:
                    updates.append({
                        "name": s.name,
                        "data": current
                    })
                    last_states[s.name] = current
            
            if updates:
                await global_status_manager.broadcast_update({
                    "type": "server_update",
                    "servers": updates
                })
            
            db.close()
        except Exception as e:
            print(f"Broadcast Error: {e}")
        
        await asyncio.sleep(2) # Update every 2 seconds

# Start the broadcast task on app startup
@router.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_server_updates())

@router.websocket("/{name}/chat")
async def websocket_chat(websocket: WebSocket, name: str):
    await websocket.accept()
    queue = server_controller.get_console_queue(name)
    
    if not queue:
        await websocket.close(code=4004, reason="Server not found")
        return
        
    import re
    # Match: [12:34:56] [Server thread/INFO]: <Username> msg
    chat_pattern = re.compile(r"\[.*INFO\]: <([^>]+)> (.*)")
    
    async def listen_to_client():
        try:
            while True:
                data = await websocket.receive_json()
                if data.get("type") == "send_chat":
                    username = data.get("username", "Admin")
                    message = data.get("message", "")
                    if message:
                        # Send to Minecraft server as a formatted message
                        # We use 'say' or 'tellraw' to make it look official
                        cmd = f'tellraw @a {{"text": "<${username}> {message}", "color": "yellow"}}'
                        await server_controller.send_command(name, cmd)
        except Exception as e:
            print(f"[WS CHAT] Client listen error: {e}")

    async def broadcast_to_client():
        try:
            while True:
                log_line = await queue.get()
                match = chat_pattern.search(log_line)
                if match:
                    sender = match.group(1)
                    message = match.group(2)
                    await websocket.send_json({
                        "type": "chat",
                        "sender": sender,
                        "message": message,
                        "is_system": False
                    })
                elif "joined the game" in log_line:
                    await websocket.send_json({
                        "type": "chat",
                        "sender": "System",
                        "message": log_line.split("INFO]: ")[1],
                        "is_system": True
                    })
                elif "left the game" in log_line:
                    await websocket.send_json({
                        "type": "chat",
                        "sender": "System",
                        "message": log_line.split("INFO]: ")[1],
                        "is_system": True
                    })
        except Exception as e:
            print(f"[WS CHAT] Broadcast error: {e}")

    # Run both tasks concurrently
    try:
        await asyncio.gather(listen_to_client(), broadcast_to_client())
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[WS CHAT] Fatal error: {e}")
    finally:
        try: await websocket.close()
        except: pass

@router.get("/{name}/export")
async def export_server(name: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Export a server as a ZIP file"""
    try:
        zip_path = await server_controller.export_server(db, name)
        return FileResponse(
            path=zip_path,
            filename=f"{name}.zip",
            media_type="application/zip",
            background=None  # File will be cleaned up by the controller
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Server not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.post("/import")
async def import_server(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import a server from a ZIP file"""
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a ZIP archive")
    
    try:
        server = await server_controller.import_server(db, file)
        return APIResponse(status="success", message=f"Server '{server.name}' imported successfully", data=server)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


# --- Player Management Endpoints ---
@router.get("/{name}/players")
def get_players_data(name: str, current_user: User = Depends(get_current_user)):
    """Get complete player data: online players, banned users, and banned IPs"""
    try:
        online_players = server_controller.get_online_players(name)
        print(f"DEBUG: API get_players for {name}: {online_players}")
        bans = server_controller.get_bans(name)
        recent = server_controller.get_recent_activity(name)
        
        return APIResponse(status="success", message="Players retrieved", data={
            "online_players": online_players if online_players else [],
            "banned_users": bans.get("players", []) if bans else [],
            "banned_ips": bans.get("ips", []) if bans else [],
            "recent_activity": recent
        })
    except Exception as e:
        print(f"ERROR: API get_players failed: {e}")
        # Return empty data instead of error to prevent frontend spam
        return APIResponse(status="success", message="No data", data={
            "online_players": [],
            "banned_users": [],
            "banned_ips": [],
            "recent_activity": []
        })



@router.post("/{name}/players/{username}/kick")
async def kick_player(name: str, username: str, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Kick a player from the server"""
    try:
        success = await server_controller.kick_player(name, username)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to kick player")
        AuditService.log_action(db, current_user, "KICK_PLAYER", request.client.host, f"Kicked {username} from {name}")
        return APIResponse(status="success", message=f"Player {username} kicked", data=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{name}/players/{username}/ban")
async def ban_player(
    name: str, 
    username: str,
    ban_data: BanRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ban a player by username, IP, or both"""
    mode = ban_data.mode
    reason = ban_data.reason
    expires = ban_data.expires # New field
    
    try:
        if mode == "username":
            success = await server_controller.ban_user(name, username, reason, expires)
        elif mode == "ip":
            # Get player's IP first
            players = server_controller.get_online_players(name)
            player = next((p for p in players if p.get("username") == username), None)
            if player and player.get("ip"):
                success = await server_controller.ban_ip(name, player["ip"], reason, username=username)
            else:
                raise HTTPException(status_code=400, detail="Player IP not found")
        elif mode == "both":
            # Ban both username and IP
            success1 = await server_controller.ban_user(name, username, reason, expires)
            players = server_controller.get_online_players(name)
            player = next((p for p in players if p.get("username") == username), None)
            if player and player.get("ip"):
                success2 = await server_controller.ban_ip(name, player["ip"], reason, username=username)
                success = success1 and success2
            else:
                success = success1
        else:
            raise HTTPException(status_code=400, detail="Invalid ban mode")
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to ban")
        AuditService.log_action(db, current_user, "BAN_PLAYER", request.client.host, f"Banned {username} from {name} mode={mode} reason={reason}")
        return APIResponse(status="success", message=f"Player {username} banned", data=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{name}/banned-players/{username}")
async def update_ban(
    name: str, 
    username: str, 
    ban_data: UpdateBanRequest, 
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update existing ban details"""
    reason = ban_data.reason
    expires = ban_data.expires
    
    try:
        success = await server_controller.update_ban(name, username, reason, expires)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update ban")
        AuditService.log_action(db, current_user, "UPDATE_BAN", request.client.host, f"Updated ban for {username} in {name}")
        return APIResponse(status="success", message=f"Ban updated for {username}", data=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{name}/players/{username}/unban")
async def unban_user(name: str, username: str, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Unban a user"""
    try:
        success = await server_controller.unban_user(name, username)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to unban user")
        AuditService.log_action(db, current_user, "UNBAN_USER", request.client.host, f"Unbanned {username} from {name}")
        return APIResponse(status="success", message=f"User {username} unbanned", data=None)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{name}/players/ip/{ip}/unban")
async def unban_ip(name: str, ip: str, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Unban an IP address"""
    try:
        success = await server_controller.unban_ip(name, ip)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to unban IP")
        AuditService.log_action(db, current_user, "UNBAN_IP", request.client.host, f"Unbanned IP {ip} from {name}")
        return APIResponse(status="success", message=f"IP {ip} unbanned", data=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{name}/players/{username}/op")
async def op_player(name: str, username: str, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        success = await server_controller.op_player(name, username)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to op player")
        AuditService.log_action(db, current_user, "OP_PLAYER", request.client.host, f"Opped {username} on {name}")
        return APIResponse(status="success", message=f"Player {username} opped", data=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{name}/players/{username}/deop")
async def deop_player(name: str, username: str, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        success = await server_controller.deop_player(name, username)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to deop player")
        AuditService.log_action(db, current_user, "DEOP_PLAYER", request.client.host, f"De-opped {username} on {name}")
        return APIResponse(status="success", message=f"Player {username} de-opped", data=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{name}/chat")
async def send_chat_message(
    name: str, 
    data: ChatRequest, 
    request: Request,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Send a chat message to the game via MasterBridge or /tellraw command"""
    text = data.text
    formatted = data.formatted  # If True, use /tellraw for admin message
    
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text' field")
    
    try:
        success = await server_controller.send_chat_message(name, text, formatted)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to send message. Server may not be online.")
        AuditService.log_action(db, current_user, "SEND_CHAT", request.client.host, f"Sent chat to {name}: {text[:50]}")
        return APIResponse(status="success", message="Chat message sent successfully", data=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# --- MasterBridge Data Endpoints Removed ---
# (Endpoints previously under /{name}/masterbridge/ have been deleted)

@router.get("/{name}/export")
async def export_server(name: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Export server as a ZIP file"""
    try:
        from app.services.minecraft.service import server_service
        zip_path = await server_service.export_server(db, name)
        return FileResponse(
            path=zip_path,
            media_type="application/zip",
            filename=f"{name}_backup.zip"
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_server(
    file: UploadFile = File(...), 
    request: Request = None, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Import server from a ZIP file"""
    try:
        from app.services.minecraft.service import server_service
        server = await server_service.import_server(db, file)
        AuditService.log_action(db, current_user, "IMPORT_SERVER", request.client.host if request else "Local", f"Imported server {server.name}")
        return APIResponse(status="success", message="Server imported successfully", data={"name": server.name})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

