from sqlalchemy.orm import Session
from app.services.minecraft import server_service
from typing import List, Optional, Dict, Any
from app.services.bitacora_service import BitacoraService
from database.models.server import Server
from core.broadcaster import broadcaster

class ServerController:
    def get_all_servers(self, db: Session) -> List[Server]:
        servers = db.query(Server).all()
        for s in servers:
            self._inject_runtime_data(s)
        return servers

    def get_server(self, db: Session, name: str) -> Optional[Server]:
        server = db.query(Server).filter(Server.name == name).first()
        if server:
            self._inject_runtime_data(server)
        return server

    def _inject_runtime_data(self, server: Server):
        process = server_service.get_process(server.name)
        if process:
            # Stats dictionary: {"status": ..., "cpu": ..., "ram": ...}
            stats = process.get_stats()
            server.status = stats["status"]
            server.cpu_usage = stats["cpu"]
            server.ram_usage = stats["ram"]  # Use model field name
            server.current_players = stats.get("players", 0)  # Use model field name
            server.disk_usage = stats.get("disk", 0)
        else:
            server.status = "OFFLINE"
            server.cpu_usage = 0
            server.ram_usage = 0
            server.current_players = 0
            server.disk_usage = 0

    def get_server_stats(self, name: str):
        process = server_service.get_process(name)
        if process:
            return process.get_stats()
        return {"status": "OFFLINE", "cpu": 0, "ram": 0, "players": 0}

    def create_server(
        self, 
        db: Session, 
        name: str, 
        version: str, 
        ram_mb: int, 
        port: int, 
        online_mode: bool,
        mod_loader: str = "VANILLA",
        cpu_cores: float = 1.0,
        disk_mb: int = 2048,
        max_players: int = 20,
        motd: str = "A Minecraft Server",
        progress_callback = None
    ):
        server = server_service.create_server(
            db, name, version, ram_mb, port, online_mode,
            mod_loader=mod_loader,
            cpu_cores=cpu_cores,
            disk_mb=disk_mb,
            max_players=max_players,
            motd=motd,
            progress_callback=progress_callback
        )

        if server:
             BitacoraService.add_log(db, "ADMIN", "SERVER_CREATE", f"Created server {name} ({version})")
        return server

    def setup_server_files(self, db: Session, server: Server, progress_callback=None):
        """Perform the actual file operations for a server record that already exists"""
        return server_service.setup_server_files(db, server, progress_callback=progress_callback)

    def update_server(self, db: Session, name: str, data: Dict[str, Any]) -> Optional[Server]:
        server = db.query(Server).filter(Server.name == name).first()
        if not server:
            return None
        
        # MasterBridge tracking removed
        
        for key, value in data.items():
            if value is not None and hasattr(server, key):
                setattr(server, key, value)
        
        db.commit()
        db.refresh(server)
        
        # MasterBridge reload removed
        
        BitacoraService.add_log(db, "ADMIN", "SERVER_UPDATE", f"Updated server {name} with {list(data.keys())}")
        
        return server

    def delete_server(self, db: Session, name: str):
        server_service.delete_server(db, name)
        BitacoraService.add_log(db, "ADMIN", "SERVER_DELETE", f"Deleted server {name}")
        return True

    async def start_server(self, name: str):
        process = server_service.get_process(name)
        if process:
            await process.start()
            BitacoraService.add_log_background("ADMIN", "SERVER_START", f"Started server {name}")
            return True
        return False

    async def stop_server(self, name: str):
        process = server_service.get_process(name)
        if process:
            await process.stop()
            BitacoraService.add_log_background("ADMIN", "SERVER_STOP", f"Stopped server {name}")
            return True
        return False
    
    def kill_server(self, name: str):
        process = server_service.get_process(name)
        if process:
            process.kill()
            BitacoraService.add_log_background("ADMIN", "SERVER_KILL", f"Killed server {name}")
            return True
        return False

    async def restart_server(self, name: str):
        # We trigger this as a sequence but the route will call it in background
        await self.stop_server(name)
        import asyncio
        await asyncio.sleep(2)
        await self.start_server(name)
        BitacoraService.add_log_background("ADMIN", "SERVER_RESTART", f"Restarted server {name}")
        return True

    async def send_command(self, name: str, command: str):
        process = server_service.get_process(name)
        if process:
            # Strip leading slash if present (commands via stdin shouldn't have it)
            clean_cmd = command.lstrip('/')
            await process.write(clean_cmd)
            BitacoraService.add_log_background("ADMIN", "SERVER_COMMAND", f"Sent command to {name}: {clean_cmd}")
            return True
        return False
    
    def get_console_queue(self, name: str):
        process = server_service.get_process(name)
        if process:
            return process.subscribe_logs()
        return None
    
    async def export_server(self, db: Session, name: str) -> str:
        """Export a server as a ZIP file"""
        return await server_service.export_server(db, name)
    
    async def import_server(self, db: Session, file):
        """Import a server from a ZIP file"""
        return await server_service.import_server(db, file)
    
    # --- Player Management ---
    def get_online_players(self, name: str):
        """Get list of online players"""
        process = server_service.get_process(name)
        if process:
            return process.get_online_players()
        return []

    def get_recent_activity(self, name: str):
        """Get recent player activity (kicks, bans, etc)"""
        process = server_service.get_process(name)
        if process and hasattr(process, 'recent_activity'):
            return process.recent_activity
        return []
    
    async def kick_player(self, name: str, username: str):
        """Kick a player"""
        process = server_service.get_process(name)
        if process:
            return await process.kick_player(username)
        return False
    
    async def ban_user(self, name: str, username: str, reason: str = "Banned by admin", expires: str = "forever"):
        """Ban a player by username"""
        process = server_service.get_process(name)
        if process:
            return await process.ban_user(username, reason, expires)
        return False

    async def update_ban(self, name: str, username: str, reason: str = None, expires: str = None):
        """Update existing ban"""
        process = server_service.get_process(name)
        if process:
            return await process.update_ban(username, reason, expires)
        return False
    
    async def ban_ip(self, name: str, ip: str, reason: str = "Banned by admin", username: str = None):
        """Ban an IP address"""
        process = server_service.get_process(name)
        if process:
            return await process.ban_ip(ip, reason, username=username)
        return False
    
    def get_bans(self, name: str):
        """Get banned players and IPs"""
        process = server_service.get_process(name)
        if process:
            return process.get_bans()
        return {"players": [], "ips": []}
    
    async def unban_user(self, name: str, username: str):
        """Unban a player"""
        process = server_service.get_process(name)
        if process:
            return await process.unban_user(username)
        return False
    
    async def unban_ip(self, name: str, ip: str):
        """Unban an IP"""
        process = server_service.get_process(name)
        if process:
            return await process.unban_ip(ip)
        return False

    async def op_player(self, name: str, username: str):
        """Op a player"""
        process = server_service.get_process(name)
        if process:
            return await process.op_player(username)
        return False
    
    async def deop_player(self, name: str, username: str):
        """Deop a player"""
        process = server_service.get_process(name)
        if process:
            return await process.deop_player(username)
        return False
    
    async def send_chat_message(self, name: str, text: str, formatted: bool = False, sender: str = "Admin"):
        """
        Send a chat message to the game
        Args:
            name: Server name
            text: Message text
            formatted: If True, sends as Admin with /tellraw
            sender: The username of the admin sending the message
        """
        process = server_service.get_process(name)
        if not process:
            return False
        
        if formatted:
            # Use /tellraw command for formatted admin message
            # Format: [Admin] sender: text
            escaped_text = text.replace('\\', '\\\\').replace('"', '\\"')
            escaped_sender = sender.replace('\\', '\\\\').replace('"', '\\"')
            
            tellraw_command = f'tellraw @a [{{"text":"<","color":"yellow"}},{{"text":"{escaped_sender}","color":"yellow"}},{{"text":"> ","color":"yellow"}},{{"text":"{escaped_text}","color":"white"}}]'
            await process.write(tellraw_command)
            
            # Also broadcast back to all apps so the sender and others see it immediately via broadcaster
            # This ensures real-time sync even for messages sent from the app
            print(f"[CONTROLLER] Broadcasting message from {sender} to {name}")
            await broadcaster.broadcast_chat(name, sender, text, is_system=False, chat_type="sent")
            
            return True
        else:
            # Fallback to standard Server Command
            await process.write(f"say {text}")
            return True
        
    # --- MasterBridge Data Retrieval Methods Removed ---
    pass


