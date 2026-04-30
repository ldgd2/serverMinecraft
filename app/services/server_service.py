import asyncio
import os
import psutil
from typing import Dict, Optional, List
import subprocess
from asyncio import subprocess as async_subprocess # Type hint use
from sqlalchemy.orm import Session
from database.models import Server
from database.connection import SessionLocal
from database.models.players.player import Player
from database.models.players.player_detail import PlayerDetail

# --- Player Manager ---
class PlayerManager:
    def __init__(self):
        # Store players as {username: {ip: str, uuid: str, joined_at: datetime}}
        self.online_players = {}

    def parse_log_line(self, line: str, update_state: bool = True):
        """
        Parse a log line and update player list.
        Returns an event dict if a relevant event occurred, else None.
        Event keys: type, user, reason, timestamp (if found)
        """
        import re
        from datetime import datetime
        
        cleaned_line = line.strip()
        timestamp = None
        
        # Extract timestamp [HH:MM:SS]
        ts_match = re.search(r'^\[(\d{2}:\d{2}:\d{2})\]', cleaned_line)
        if ts_match:
            # We don't have date here, caller might handle date
            timestamp = ts_match.group(1)

        # Pattern 1: UUID (Info only, doesn't change online state but useful)
        # "UUID of player Username is uuid-here"
        if "UUID of player" in cleaned_line:
            match = re.search(r'UUID of player (\S+) is ([a-f0-9-]+)', cleaned_line)
            if match:
                username = match.group(1)
                uuid = match.group(2)
                if update_state:
                    if username not in self.online_players:
                        self.online_players[username] = {}
                    self.online_players[username]['uuid'] = uuid
                return None # No state change yet

        # Pattern 2: Login (Technical - contains IP)
        # "Username[/IP:port] logged in with entity id..."
        # Regex to capture Username, IP
        match_login = re.search(r':\s(\S+)\[/([0-9.]+):\d+\]\slogged\sin', cleaned_line)
        if match_login:
            username = match_login.group(1)
            ip = match_login.group(2)
            
            if update_state:
                if username not in self.online_players:
                    self.online_players[username] = {}
                
                self.online_players[username]['ip'] = ip
                if 'joined_at' not in self.online_players[username]:
                     self.online_players[username]['joined_at'] = datetime.now().isoformat()
            
            return {'type': 'join', 'user': username, 'reason': 'Joined the game', 'timestamp': timestamp}

        # Pattern 3: Join Message (Visible to players)
        # "Username joined the game"
        match_join_msg = re.search(r':\s(\S+)\sjoined\sthe\sgame', cleaned_line)
        if match_join_msg:
            username = match_join_msg.group(1)
            if update_state:
                if username not in self.online_players:
                    self.online_players[username] = {'joined_at': datetime.now().isoformat()}
            return {'type': 'join', 'user': username, 'reason': 'Joined the game', 'timestamp': timestamp}

        # Pattern 4: Lost Connection (Generic disconnect/timeout/kick)
        # "Username lost connection: Reason"
        match_lost = re.search(r':\s(\S+)\slost\sconnection:\s(.*)', cleaned_line)
        if match_lost:
            username = match_lost.group(1)
            reason = match_lost.group(2)
            if update_state:
                if username in self.online_players:
                    data = self.online_players.pop(username)
                    joined_at = data.get('joined_at')
                else:
                    joined_at = None
                
            # Refine reason for event log
            event_type = 'leave'
            if "Kicked" in reason or "kicked" in reason:
                event_type = 'kick'
            elif "Timed out" in reason:
                event_type = 'leave' # or timeout
                
            return {'type': event_type, 'user': username, 'reason': reason, 'timestamp': timestamp, 'joined_at': joined_at}

        # Pattern 5: Left the game (Voluntary or consequence of lost connection)
        # "Username left the game"
        match_left = re.search(r':\s(\S+)\sleft\sthe\sgame', cleaned_line)
        if match_left:
            username = match_left.group(1)
            if update_state:
                if username in self.online_players:
                    data = self.online_players.pop(username)
                    return {'type': 'leave', 'user': username, 'reason': 'Left the game', 'timestamp': timestamp, 'joined_at': data.get('joined_at')}
            else:
                 return {'type': 'leave', 'user': username, 'reason': 'Left the game', 'timestamp': timestamp}
            
            # If not in list (already removed), and update_state=True, we suppress?
            # User wants robust detection for logs too.
            # If we already processed lost connection, user is gone.
            # If update_state is False (history scan), we generally want to see the event.
            return None

        # Pattern 6: Console Kicks/Bans (Explicit)
        if "Kicked " in cleaned_line and " lost connection" not in cleaned_line:
             match_kick = re.search(r'Kicked ([a-zA-Z0-9_]+): (.*)', cleaned_line)
             if match_kick:
                 return {'type': 'kick', 'user': match_kick.group(1), 'reason': match_kick.group(2), 'timestamp': timestamp}

        if "Banned " in cleaned_line and " IP " not in cleaned_line:
            match_ban = re.search(r'Banned ([a-zA-Z0-9_]+): (.*)', cleaned_line)
            if match_ban:
                return {'type': 'ban', 'user': match_ban.group(1), 'reason': match_ban.group(2), 'timestamp': timestamp}
        
        if "Banned IP " in cleaned_line:
             match_banip = re.search(r'Banned IP ([0-9.]+): (.*)', cleaned_line)
             if match_banip:
                 return {'type': 'ban-ip', 'user': match_banip.group(1), 'reason': match_banip.group(2), 'timestamp': timestamp}

        if "Unbanned " in cleaned_line and " IP " not in cleaned_line:
             match_unban = re.search(r'Unbanned ([a-zA-Z0-9_]+)', cleaned_line)
             if match_unban:
                  return {'type': 'unban', 'user': match_unban.group(1), 'reason': 'Unbanned', 'timestamp': timestamp}

        if "Unbanned IP " in cleaned_line:
             match_unbanip = re.search(r'Unbanned IP ([0-9.]+)', cleaned_line)
             if match_unbanip:
                  return {'type': 'unban-ip', 'user': match_unbanip.group(1), 'reason': 'Unbanned IP', 'timestamp': timestamp}
                  
        return None

    def get_players(self):
        return [
            {"username": u, **d} 
            for u, d in self.online_players.items()
        ]
    
    def get_count(self):
        return len(self.online_players)

# --- Process Logic (Internal to Service) ---
class MinecraftProcess:
    def __init__(self, name: str, ram_mb: int, jar_path: str, working_dir: str, server_id: int):
        self.name = name
        self.server_id = server_id
        self.ram_mb = ram_mb
        self.jar_path = jar_path
        self.working_dir = working_dir
        self.working_dir = working_dir
        self.process: Optional[async_subprocess.Process] = None
        self.log_subscribers: List[asyncio.Queue] = []
        self._status = "OFFLINE" # OFFLINE, STARTING, ONLINE, STOPPING
        self.current_players = 0
        self.player_manager = PlayerManager()
        self.recent_activity = [] # List of {type, user, reason, time}
        
        # Load activity history on startup
        try:
            self.load_activity_history()
        except: pass

    @property
    def status(self):
        # Fallback if process died unexpectedly
        if self._status != "OFFLINE" and not self.is_process_alive():
             self._status = "OFFLINE"
        return self._status
    
    async def start(self):
        if self.is_running():
            print(f"Server {self.name} is already running.")
            return

        print(f"DEBUG: Starting server {self.name}")
        print(f"DEBUG: Working dir: {self.working_dir}")
        print(f"DEBUG: Jar path: {self.jar_path}")
        self._status = "STARTING"

        # --- FORGE STARTUP LOGIC ---
        # Modern Forge (1.17+) uses user_jvm_args.txt and libraries
        # We need to detect if we should run the "run.bat" equivalent or the jar
        
        # Check for run.bat or run.sh to infer args if possible, or just standard Forge structure
        # Actually better to construct the java command ourselves if possible to keep control
        # But parsing the args file is complex. 
        # Simpler approach: check if 'run.bat' exists (created by installer) and if so, see what it does?
        # Or look for 'user_jvm_args.txt'
        
        cmd = []
        is_modern_forge = False
        
        # Check for modern Forge structure
        args_file = os.path.join(self.working_dir, "user_jvm_args.txt")
        run_bat = os.path.join(self.working_dir, "run.bat")
        run_sh = os.path.join(self.working_dir, "run.sh")
        
        has_run_script = os.path.exists(run_bat) or os.path.exists(run_sh)
        
        if os.path.exists(args_file) and has_run_script:
            is_modern_forge = True
            
            # --- Configure RAM in user_jvm_args.txt ---
            # Read existing
            lines = []
            try:
                with open(args_file, "r") as f:
                    lines = f.readlines()
            except: pass
            
            # Filter out old memory args
            new_lines = [l for l in lines if not l.strip().startswith("-Xmx") and not l.strip().startswith("-Xms")]
            
            # Append new memory args
            new_lines.append(f"\n-Xmx{self.ram_mb}M\n")
            new_lines.append(f"-Xms{max(512, self.ram_mb // 2)}M\n")
            
            with open(args_file, "w") as f:
                f.writelines(new_lines)
                
            # --- Construct Command ---
            # We want to mimic what run.bat/sh does but run java directly for PID control.
            # run.bat/sh usually does: java @user_jvm_args.txt @libraries/net/.../win_args.txt %*
            
            # Find the win_args.txt (or unix_args.txt)
            win_args_path = None
            libraries_dir = os.path.join(self.working_dir, "libraries")
            if os.path.exists(libraries_dir):
                for root, dirs, files in os.walk(libraries_dir):
                    for file in files:
                        if (file == "win_args.txt" or file == "unix_args.txt") and "minecraftforge" in root:
                            win_args_path = os.path.join(root, file)
                            break
                    if win_args_path: break
            
            if win_args_path:
                rel_win_args = os.path.relpath(win_args_path, self.working_dir)
                cmd = [
                    "java",
                    # Memory args are in user_jvm_args.txt now, so we don't repeat them here
                    f"@{os.path.basename(args_file)}",
                    f"@{rel_win_args}",
                    "nogui"
                ]
            else:
                 # Fallback: Just try to run the script directly? 
                 # But we lose PID control. 
                 # Let's hope win_args is found if it's modern forge.
                 # If not, maybe it's 1.17 pure? 
                 print("DEBUG: Modern Forge detected but args file not found. Trying standard JAR start as fallback.")
                 is_modern_forge = False # Fallback to jar
        else:
             is_modern_forge = False

        if not is_modern_forge:
             cmd = [
                "java",
                f"-Xmx{self.ram_mb}M",
                f"-Xms{max(512, self.ram_mb // 2)}M",
                "-jar",
                self.jar_path,
                "nogui"
            ]
        
        print(f"DEBUG: Command: {' '.join(cmd)}")
        
        try:
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.working_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
            print(f"DEBUG: Process started with PID {self.process.pid}")
            
            # --- Persist PID ---
            pid_file = os.path.join(self.working_dir, "server.pid")
            with open(pid_file, "w") as f:
                f.write(str(self.process.pid))
                
            asyncio.create_task(self._tail_log_file())
        except FileNotFoundError:
            print(f"Error: Working directory or Java not found for {self.name}")
            self.process = None
            self._status = "OFFLINE"
            raise Exception(f"Server configuration error: Directory or Java not found. Re-saving settings might fix this.")
        except Exception as e:
            print(f"Error starting server {self.name}: {e}")
            self.process = None
            self._status = "OFFLINE"
            raise
        
        # Start background task to monitor process and ensure status cleanup
        asyncio.create_task(self._monitor_process())

    async def _monitor_process(self):
        """Monitor process and ensure state is updated when it dies"""
        if not self.process:
            return
            
        try:
            # Wait for process to finish
            await self.process.wait()
            print(f"INFO: Process for {self.name} has terminated")
            
            # Give tail_log a moment to finish cleanup
            await asyncio.sleep(1)
            
            # Force cleanup if status is still not OFFLINE
            if self._status != "OFFLINE":
                print(f"WARN: Process dead but status is {self._status}, forcing OFFLINE")
                self._cleanup_pid()
        except Exception as e:
            print(f"ERROR: Error in process monitor for {self.name}: {e}")

    async def stop(self):
        if not self.is_running():
            print(f"INFO: Server {self.name} is already stopped")
            self._status = "OFFLINE"  # Ensure status is OFFLINE
            return
        try:
            self._status = "STOPPING"
            print(f"INFO: Stopping server {self.name}")
            await self.write("stop")
            try:
                if self.process:
                    await asyncio.wait_for(self.process.wait(), timeout=10.0)
                else:
                    # If we recovered via PID but don't have process obj, check via psutil
                    self._wait_for_pid_exit(timeout=10.0)
            except asyncio.TimeoutError:
                print(f"WARN: Server {self.name} didn't stop gracefully, killing...")
                self.kill()
                
            # IMPORTANT: Set to OFFLINE after process ends
            self._status = "OFFLINE"
            self.current_players = 0
            print(f"INFO: Server {self.name} stopped successfully - status set to OFFLINE")
        except Exception as e:
            print(f"ERROR: Error stopping server {self.name}: {e}")
            self.kill()  # Force kill on error
            
    def _wait_for_pid_exit(self, timeout=10.0):
        # Simplistic wait for recovered processes
        import time
        start = time.time()
        pid = self._get_pid()
        if not pid: return
        while time.time() - start < timeout:
            if not psutil.pid_exists(pid):
                return
            time.sleep(0.5)

    def kill(self):
        print(f"INFO: Force killing server {self.name}")
        pid = self._get_pid()
        if pid:
            try:
                p = psutil.Process(pid)
                p.kill()
                print(f"INFO: Process {pid} killed successfully")
            except psutil.NoSuchProcess:
                print(f"INFO: Process {pid} already dead")
        self._cleanup_pid()
        self.current_players = 0

    def _cleanup_pid(self):
        pid_file = os.path.join(self.working_dir, "server.pid")
        if os.path.exists(pid_file):
            try: os.remove(pid_file)
            except: pass
        self.process = None
        self._status = "OFFLINE"
        print(f"INFO: Cleanup complete for {self.name} - status set to OFFLINE")

    def _get_pid(self):
        if self.process: return self.process.pid
        # Check pid file
        pid_file = os.path.join(self.working_dir, "server.pid")
        if os.path.exists(pid_file):
            try:
                with open(pid_file, "r") as f:
                    return int(f.read().strip())
            except: pass
        return None

    async def write(self, command: str):
        if self.process and self.process.stdin:
            self.process.stdin.write(f"{command}\n".encode())
            await self.process.stdin.drain()
        else:
            # Cannot write to recovered process without RCON or similar
            print(f"WARNING: Cannot write to {self.name} (Recovered process has no stdin access)")

    def _add_activity(self, type: str, user: str, reason: str = None, timestamp: str = None):
         from datetime import datetime
         if not hasattr(self, 'recent_activity'): self.recent_activity = []
         
         if not timestamp:
             timestamp = datetime.now().isoformat()
         
         # Check duplicates (in memory)
         # We check strictly against the last few items to avoid adding the same event twice
         # especially when recovering context.
         is_dup = False
         for item in self.recent_activity[:10]: # Check last 10
             if item['type'] == type and item['user'] == user and item['timestamp'] == timestamp:
                 is_dup = True
                 break
         
         if is_dup: return

         # Append to persistent log file
         log_file = os.path.join(self.working_dir, "logs", "user_connections.log")
         try:
             # Ensure directory exists (it should)
             os.makedirs(os.path.dirname(log_file), exist_ok=True)
             with open(log_file, "a", encoding="utf-8") as f:
                 f.write(f"{timestamp} | {type} | {user} | {reason or ''}\n")
         except Exception as e:
             print(f"WARN: Failed to write to activity log: {e}")

         self.recent_activity.insert(0, {
             "type": type,
             "user": user,
             "reason": reason,
             "timestamp": timestamp
         })
         # Keep last 50
         if len(self.recent_activity) > 50:
             self.recent_activity.pop()
    
    
    # --- DB Persistence ---
    async def _persist_event_to_db(self, event):
        await asyncio.get_event_loop().run_in_executor(None, self._sync_persist_event, event)

    def _sync_persist_event(self, event):
        session = SessionLocal()
        try:
            import datetime
            import uuid as uuid_lib
            
            username = event.get('user')
            if not username: return
            
            # Get UUID logic
            # For 'join', uuid might be in self.player_manager (but race condition if looking at live dict?)
            # Actually, the tail loop runs linearly? Yes.
            # But 'leave' removed it from dict.
            # However, we can try to find existing player in DB first.
            
            # Heuristic: Try to find existing player by name in this server
            player = session.query(Player).filter_by(server_id=self.server_id, name=username).first()
            
            player_uuid = None
            if player:
                player_uuid = player.uuid
            else:
                 # If not in DB, we need UUID.
                 # Check PlayerManager cache (might have it if they just joined/left and it wasn't purged immediately? No, it pops on leave)
                 # But we might have cached it in a separate persistent map?
                 # Or generate offline UUID if we cant find it.
                 # Ideally, 'join' event context should carry UUID if we extracted it.
                 # But 'join' regex doesn't have UUID. UUID log line does.
                 # We can store UUID history in PlayerManager.
                 pass
            
            # Temporary: Generate Offline UUID if missing
            if not player_uuid:
                 player_uuid = str(uuid_lib.uuid3(uuid_lib.NAMESPACE_DNS, username))
            
            # Upsert Player
            if not player:
                player = Player(uuid=player_uuid, server_id=self.server_id, name=username)
                session.add(player)
                session.flush()
            
            # Upsert Details
            detail = session.query(PlayerDetail).filter_by(player_uuid=player_uuid, server_id=self.server_id).first()
            if not detail:
                detail = PlayerDetail(player_uuid=player_uuid, server_id=self.server_id)
                session.add(detail)
                
            now = datetime.datetime.now()
            
            if event['type'] == 'join':
                detail.last_joined_at = now
                # IP?
                # PlayerManager tracks IP in memory.
                # If we are in 'join', user is in memory.
                p_data = self.player_manager.online_players.get(username)
                if p_data and p_data.get('ip'):
                    detail.last_ip = p_data.get('ip')
                    
            elif event['type'] in ['leave', 'kick']:
                # Calculate playtime
                # We need joined_at from event (we added it to return val in PlayerManager)
                joined_at_iso = event.get('joined_at')
                if joined_at_iso:
                    try:
                        joined_dt = datetime.datetime.fromisoformat(joined_at_iso)
                        delta = (now - joined_dt).total_seconds()
                        if delta > 0:
                            if detail.total_playtime_seconds is None:
                                detail.total_playtime_seconds = 0
                            detail.total_playtime_seconds += int(delta)
                    except: pass
            
            session.commit()
            
        except Exception as e:
            print(f"DB Error persisting event: {e}")
            session.rollback()
        finally:
            session.close()

    # --- Player Management Methods ---
    def get_online_players(self):
        """Get list of currently online players with their info"""
        return self.player_manager.get_players()
    
    async def kick_player(self, username: str):
        """Kick a player from the server"""
        if not self.is_running() or self._status != "ONLINE":
            return False
        await self.write(f"kick {username}")
        print(f"INFO: Kicked player {username} from {self.name}")
        return True
    
    async def ban_user(self, username: str, reason: str = "Banned by admin", expires: str = "forever"):
        """Ban a player by username with optional expiration"""
        import json
        from datetime import datetime
        
        if not self.is_running() or self._status != "ONLINE":
            return False
        
        # Execute ban command (Standard 'ban' is forever/permanent in vanilla)
        # If expires is set, vanilla 'ban' is still generic.
        # We rely on writing to the JSON file for the actual expiration logic to be respected by server (on restart/reload)
        # or implies this is a cosmetic record if vanilla doesn't support tempban.
        # However, writing to JSON is the requested way.
        
        await self.write(f"ban {username} {reason}")
        
        # Update banned-players.json
        ban_file = os.path.join(self.working_dir, "banned-players.json")
        bans = []
        if os.path.exists(ban_file):
            try:
                with open(ban_file, 'r') as f:
                    bans = json.load(f)
            except: pass
        
        # Remove existing if any (to update)
        bans = [b for b in bans if b.get('name') != username]
        
        # Add new ban
        uuid = self.player_manager.online_players.get(username, {}).get('uuid', 'unknown')
        
        # If uuid is unknown, try to find it in previous bans or usercache? 
        # For now 'unknown' or try to reuse existing UUID if re-banning?
        
        record = {
            "uuid": uuid,
            "name": username,
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S %z"),
            "source": "Server",
            "expires": expires,
            "reason": reason
        }
        bans.append(record)
        
        try:
            with open(ban_file, 'w') as f:
                json.dump(bans, f, indent=2)
            # Force reload of bans?
            await self.write("banlist reload") # Spigot/Paper specific? or reload?
            # Vanilla uses 'pardon' then 'ban' to reload? No.
            # Usually files are read on startup or reload.
        except Exception as e:
            print(f"ERROR: Could not write ban file: {e}")
            
        print(f"INFO: Banned user {username} from {self.name}")
        return True

    async def update_ban(self, username: str, reason: str = None, expires: str = None):
        """Update an existing ban record"""
        import json
        ban_file = os.path.join(self.working_dir, "banned-players.json")
        if not os.path.exists(ban_file): return False
        
        try:
            with open(ban_file, 'r') as f:
                bans = json.load(f)
                
            updated = False
            for b in bans:
                if b.get('name') == username:
                    if reason: b['reason'] = reason
                    if expires: b['expires'] = expires
                    updated = True
                    break
            
            if updated:
                with open(ban_file, 'w') as f:
                    json.dump(bans, f, indent=2)
                # To apply changes effectively without restarting, we might need to unban and reban?
                # Or just reload.
                return True
        except Exception as e:
            print(f"ERROR: Failed to update ban: {e}")
        return False
    
    async def ban_ip(self, ip: str, reason: str = "Banned by admin", username: str = None):
        """Ban an IP address"""
        import json
        from datetime import datetime
        
        if not self.is_running() or self._status != "ONLINE":
            return False
        
        # Execute ban command
        await self.write(f"ban-ip {ip} {reason}")
        
        # Update banned-ips.json
        ban_file = os.path.join(self.working_dir, "banned-ips.json")
        bans = []
        if os.path.exists(ban_file):
            try:
                with open(ban_file, 'r') as f:
                    bans = json.load(f)
            except: pass
        
        # Add new ban if not already banned
        already_banned = any(b.get('ip') == ip for b in bans)
        if not already_banned:
            record = {
                "ip": ip,
                "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S %z"),
                "source": "Server",
                "expires": "forever",
                "reason": reason
            }
            if username:
                record["name"] = username # Store username for UI display
                
            bans.append(record)
            with open(ban_file, 'w') as f:
                json.dump(bans, f, indent=2)
        
        print(f"INFO: Banned IP {ip} from {self.name}")
        return True
    
    def get_bans(self):
        """Get lists of banned players and IPs"""
        import json
        
        players = []
        ips = []
        
        # Read banned-players.json
        player_ban_file = os.path.join(self.working_dir, "banned-players.json")
        if os.path.exists(player_ban_file):
            try:
                with open(player_ban_file, 'r') as f:
                    players = json.load(f)
            except: pass
        
        # Read banned-ips.json
        ip_ban_file = os.path.join(self.working_dir, "banned-ips.json")
        if os.path.exists(ip_ban_file):
            try:
                with open(ip_ban_file, 'r') as f:
                    ips = json.load(f)
            except: pass
        
        return {"players": players, "ips": ips}
    
    async def unban_user(self, username: str):
        """Unban a player"""
        import json
        
        if not self.is_running() or self._status != "ONLINE":
            return False
        
        # Execute un ban command
        await self.write(f"pardon {username}")
        
        # Update banned-players.json
        ban_file = os.path.join(self.working_dir, "banned-players.json")
        if os.path.exists(ban_file):
            try:
                with open(ban_file, 'r') as f:
                    bans = json.load(f)
                bans = [b for b in bans if b.get('name') != username]
                with open(ban_file, 'w') as f:
                    json.dump(bans, f, indent=2)
            except Exception as e:
                print(f"ERROR: Could not update ban file: {e}")
        
        print(f"INFO: Unbanned user {username} from {self.name}")
        return True
    
    async def unban_ip(self, ip: str):
        """Unban an IP address"""
        import json
        
        if not self.is_running() or self._status != "ONLINE":
            return False
        
        # Execute unban command
        await self.write(f"pardon-ip {ip}")
        
        # Update banned-ips.json
        ban_file = os.path.join(self.working_dir, "banned-ips.json")
        if os.path.exists(ban_file):
            try:
                with open(ban_file, 'r') as f:
                    bans = json.load(f)
                bans = [b for b in bans if b.get('ip') != ip]
                with open(ban_file, 'w') as f:
                    json.dump(bans, f, indent=2)
            except Exception as e:
                print(f"ERROR: Could not update ban file: {e}")
        
        print(f"INFO: Unbanned IP {ip} from {self.name}")
        return True

    def is_process_alive(self):
        pid = self._get_pid()
        if not pid: return False
        return psutil.pid_exists(pid)

    def is_running(self):
        return self.is_process_alive()


    # --- Log Parsing Delegate ---
    def _parse_line_event(self, line: str, default_date: str = None):
        """Delegate parsing to PlayerManager"""
        # If default_date is provided (history scan), do NOT update state.
        # If default_date is None (live tail), DO update state.
        update_state = (default_date is None)
        
        event = self.player_manager.parse_log_line(line, update_state=update_state)
        
        if event:
            # Update current_players count if state was updated
            if update_state:
                self.current_players = self.player_manager.get_count()
                
            # Handle timestamp
            if event.get('timestamp'):
                 if default_date:
                     event['timestamp'] = f"{default_date}T{event['timestamp']}"
                 elif 'T' not in event['timestamp']:
                     # Live tail: prepend today's date if missing (PlayerManager only returns Time)
                     from datetime import datetime
                     event['timestamp'] = f"{datetime.now().strftime('%Y-%m-%d')}T{event['timestamp']}"
            
            return event
        return None

    def _initialize_history_file(self, target_file):
        """Scan compressed logs and latest.log to populate history file"""
        import gzip
        import glob
        from datetime import datetime
        
        log_dir = os.path.join(self.working_dir, "logs")
        if not os.path.exists(log_dir): return
        
        # Ensure dir
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        
        gz_files = glob.glob(os.path.join(log_dir, "*.log.gz"))
        gz_files.sort(key=os.path.getmtime, reverse=True)
        # Limit to last 10
        gz_to_read = gz_files[:10]
        
        events = []
        
        # 1. Read Archives
        for gz_file in reversed(gz_to_read):
            try:
                # Infer date from filename or mtime
                base = os.path.basename(gz_file)
                date_part = base.split('.')[0].rsplit('-', 1)[0]
                if not re.match(r'\d{4}-\d{2}-\d{2}', date_part):
                     date_part = datetime.fromtimestamp(os.path.getmtime(gz_file)).strftime('%Y-%m-%d')
                
                with gzip.open(gz_file, 'rt', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        event = self._parse_line_event(line, default_date=date_part)
                        if event:
                            events.append(event)
            except Exception as e:
                print(f"WARN: Failed to process archive {gz_file}: {e}")

        # 2. Read latest.log (for offline server history not yet archived)
        latest_log = os.path.join(log_dir, "latest.log")
        if os.path.exists(latest_log):
             try:
                # Use file modified date as base date
                date_part = datetime.fromtimestamp(os.path.getmtime(latest_log)).strftime('%Y-%m-%d')
                with open(latest_log, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        event = self._parse_line_event(line, default_date=date_part)
                        if event:
                            events.append(event)
             except Exception as e:
                 print(f"WARN: Failed to process latest.log for history: {e}")
                
        # Write events to file
        try:
            with open(target_file, "w", encoding="utf-8") as f:
                for e in events:
                    f.write(f"{e.get('timestamp')} | {e.get('type')} | {e.get('user')} | {e.get('reason')}\n")
        except Exception as e:
            print(f"ERROR: Could not write history file: {e}")

    def load_activity_history(self):
        """Load recent activity from user_connections.log"""
        log_file = os.path.join(self.working_dir, "logs", "user_connections.log")
        
        # Initialize if missing
        if not os.path.exists(log_file):
            self._initialize_history_file(log_file)
            
        # Read last 100 lines for memory
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    # Filter existing in memory if any
                    self.recent_activity = []
                    for line in reversed(lines[-100:]):
                        parts = line.strip().split(" | ")
                        if len(parts) >= 3:
                            self.recent_activity.append({
                                "timestamp": parts[0],
                                "type": parts[1],
                                "user": parts[2],
                                "reason": parts[3] if len(parts) > 3 else None
                            })
            except Exception as e:
                print(f"WARN: Failed to load activity history: {e}")

    async def _tail_log_file(self):
        log_file_path = os.path.join(self.working_dir, "logs", "latest.log")
        start_time = asyncio.get_event_loop().time()
        
        # Wait for log file to appear if not exists
        retries = 20
        while not os.path.exists(log_file_path) and retries > 0:
            await asyncio.sleep(0.5)
            retries -= 1
            
        if not os.path.exists(log_file_path):
             print(f"WARNING: Log file not found for {self.name}")
             return

        # Tail logic
        try:
            with open(log_file_path, "r", encoding='utf-8', errors='replace') as f:
                f.seek(0, os.SEEK_END)
                if f.tell() < 10000: # If small, read from start
                    f.seek(0)
                else: 
                     # Initial context - Read last 1MB to recover state
                     seek_pos = max(0, f.tell() - 1024 * 1024)
                     f.seek(seek_pos)
                
                while self.is_running():
                    line = f.readline()
                    
                    if not self.is_running():
                        print(f"INFO: Process died during tail for {self.name}, exiting tail loop")
                        break
                    
                    if not line:
                        await asyncio.sleep(0.5)
                        if self._status == "STARTING" and (asyncio.get_event_loop().time() - start_time) > 60:
                            print(f"INFO: Server {self.name} running for >60s without errors, setting to ONLINE")
                            self._status = "ONLINE"
                        if not self.is_running(): 
                            break
                        continue
                        
                    cleaned_line = line.strip()
                    print(f"[{self.name}] {cleaned_line}")
                    
                    # --- Status Detection ---
                    if "Done (" in cleaned_line:
                        print(f"INFO: Server {self.name} is now ONLINE")
                        self._status = "ONLINE"
                    elif "Dedicated server took" in cleaned_line:
                        print(f"INFO: Server {self.name} is now ONLINE (Forge detected)")
                        self._status = "ONLINE"
                    elif "Server started" in cleaned_line:
                        print(f"INFO: Server {self.name} is now ONLINE (generic detection)")
                        self._status = "ONLINE"
                    elif "Stopping server" in cleaned_line or "Stopping the server" in cleaned_line:
                        self._status = "STOPPING"
                        print(f"INFO: Server {self.name} is now STOPPING")
                    
                    # --- Event Detection (Delegated) ---
                    event = self._parse_line_event(cleaned_line)
                    if event:
                        self._add_activity(event['type'], event['user'], event.get('reason'), event.get('timestamp'))
                        # Persist to DB (Async wrapper)
                        if event.get('type') in ['join', 'leave', 'kick', 'ban', 'ban-ip', 'unban', 'unban-ip']:
                             asyncio.create_task(self._persist_event_to_db(event))

                    for queue in self.log_subscribers:
                        await queue.put(cleaned_line)
                        
        except Exception as e:
            print(f"ERROR: Error tailing log for {self.name}: {e}")
            
        print(f"INFO: Tailing finished for {self.name}, calling cleanup")
        self._cleanup_pid()
        self.current_players = 0

    def subscribe_logs(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self.log_subscribers.append(q)
        return q

    def unsubscribe_logs(self, q: asyncio.Queue):
        if q in self.log_subscribers:
            self.log_subscribers.remove(q)

    def get_stats(self):
        """Get server stats by reading latest.log directly for reliable state detection"""
        pid = self._get_pid()
        
        # Check if process exists
        if not pid or not psutil.pid_exists(pid):
            self._status = "OFFLINE"
            return {"status": "OFFLINE", "cpu": 0, "ram": 0, "players": 0}
        
        # Process exists, read log file to determine actual status
        log_file = os.path.join(self.working_dir, "logs", "latest.log")
        status_from_log = "STARTING"  # Default if process running but no log
        
        if os.path.exists(log_file):
            try:
                # Read last 50 lines of log to determine status
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    # Seek to end and read last ~5KB
                    f.seek(0, os.SEEK_END)
                    file_size = f.tell()
                    f.seek(max(0, file_size - 5000))
                    tail = f.read()
                    
                    lines = tail.strip().split('\n')
                    
                    # Check for patterns in reverse order (most recent first)
                    has_done = False
                    has_stopping = False
                    has_terminated = False
                    
                    for line in reversed(lines[-50:]):  # Last 50 lines
                        if "Done (" in line or "Done preparing level" in line:
                            has_done = True
                        if "Stopping server" in line or "Stopping the server" in line:
                            has_stopping = True
                        if "Awaiting termination" in line or "All RegionFile I/O tasks to complete" in line:
                            has_terminated = True
                    
                    # Determine status based on patterns
                    if has_terminated or has_stopping:
                        status_from_log = "STOPPING"
                        if has_terminated:  # Fully terminated
                            self._status = "OFFLINE"
                            return {"status": "OFFLINE", "cpu": 0, "ram": 0, "players": 0}
                    elif has_done:
                        status_from_log = "ONLINE"
                    else:
                        status_from_log = "STARTING"
                    
                    self._status = status_from_log
            except Exception as e:
                print(f"ERROR: Could not read log file for {self.name}: {e}")
        
        # Get CPU/RAM stats
        try:
            sys_proc = psutil.Process(pid)
            with sys_proc.oneshot():
                cpu = sys_proc.cpu_percent()
                mem = int(sys_proc.memory_info().rss / (1024 * 1024))
            return {"status": self._status, "cpu": cpu, "ram": mem, "players": self.current_players, "recent_activity": getattr(self, 'recent_activity', [])}
        except psutil.NoSuchProcess:
            self._status = "OFFLINE"
            return {"status": "OFFLINE", "cpu": 0, "ram": 0, "players": 0}

    def _find_pid_by_scanning(self):
        # Scan for java process running in this directory
        try:
            current_cwd = os.path.abspath(self.working_dir)
            for p in psutil.process_iter(['pid', 'name', 'cwd']):
                try:
                    if p.info['name'] and 'java' in p.info['name'].lower():
                        p_cwd = p.info['cwd']
                        if p_cwd and os.path.abspath(p_cwd) == current_cwd:
                            return p.info['pid']
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception as e:
            print(f"Error scanning for PID: {e}")
        return None

    def attempt_recovery(self):
        # 1. Try generic PID (mem or file)
        pid = self._get_pid()
        
        # 2. If not found, deep scan
        if not pid:
            pid = self._find_pid_by_scanning()
            if pid:
                print(f"DEBUG: Found orphaned server process {pid} for {self.name}")
                # Self-heal: write PID file
                try:
                    with open(os.path.join(self.working_dir, "server.pid"), "w") as f:
                        f.write(str(pid))
                except: pass
                
        # 3. Verify it's actually alive
        if pid and psutil.pid_exists(pid):
            return True
        
        # Clean up stale PID file if process dead
        if pid: self._cleanup_pid()
        return False

# --- Service Manager ---
class ServerService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServerService, cls).__new__(cls)
            cls._instance.servers = {} # type: Dict[str, MinecraftProcess]
            cls._instance.base_dir = os.path.abspath("servers")
        return cls._instance

    def load_servers_from_db(self, db: Session):
        server_records = db.query(Server).all()
        for record in server_records:
            jar_path = os.path.join(self.base_dir, record.name, "server.jar")
            working_dir = os.path.join(self.base_dir, record.name)
            
            instance = MinecraftProcess(
                name=record.name,
                ram_mb=record.ram_mb,
                jar_path=jar_path,
                working_dir=working_dir,
                server_id=record.id
            )
            
            # --- Attempt Recovery ---
            if instance.attempt_recovery():
                print(f"INFO: Recovered active server {record.name}")
                instance._status = "ONLINE"
                asyncio.create_task(instance._tail_log_file())
                
            self.servers[record.name] = instance

    def get_process(self, name: str) -> MinecraftProcess:
        return self.servers.get(name)

    def create_server(
        self, 
        db: Session, 
        name: str, 
        version: str, 
        ram_mb: int, 
        port: int, 
        online_mode: bool = False,
        mod_loader: str = "VANILLA",
        cpu_cores: float = 1.0,
        disk_mb: int = 2048,
        max_players: int = 20,
        motd: str = "A Minecraft Server"
    ):
        if name in self.servers:
            raise ValueError("Server already exists")
            
        # 0. Port Check & Auto-Assign
        # Check if port is taken by another server in DB
        used_ports = [s.port for s in db.query(Server).all()]
        
        # If port is in use, or we want random (let's say we check collision)
        import random
        retries = 10
        original_port = port
        while port in used_ports or not self.is_port_free(port):
            print(f"Port {port} in use. Finding new port...")
            port = random.randint(25565, 25600)
            retries -= 1
            if retries <= 0:
                 raise ValueError(f"Could not find a free port. Requested {original_port} was taken.")
                 
        if port != original_port:
             print(f"Assigned new port: {port}")

        # 1. Locate Source Jar
        # Logic matches VersionService storage structure
        versions_root = os.path.abspath("source/versions")
        if mod_loader == "VANILLA":
            source_jar = os.path.join(versions_root, "vanilla", version, "server.jar")
        else:
            source_jar = os.path.join(versions_root, "modLoader", mod_loader.lower(), version, "server.jar")
            
        if not os.path.exists(source_jar):
            # Try finding any jar if server.jar doesn't exist
            parent_dir = os.path.dirname(source_jar)
            if os.path.exists(parent_dir):
                files = [f for f in os.listdir(parent_dir) if f.endswith(".jar")]
                if files:
                    source_jar = os.path.join(parent_dir, files[0])
                else:
                     raise ValueError(f"Version {version} for {mod_loader} not found (No JAR file). Please download it first.")
            else:
                 raise ValueError(f"Version {version} for {mod_loader} not found. Please download it first.")

        # 2. Check Disk Space (filesize vs limit)
        import shutil
        jar_size = os.path.getsize(source_jar)
        if jar_size > (disk_mb * 1024 * 1024):
             raise ValueError(f"Server JAR ({jar_size/1024/1024:.2f}MB) exceeds allocated disk space ({disk_mb}MB)")

        # 3. Create Server Directory
        server_dir = os.path.join(self.base_dir, name)
        os.makedirs(server_dir, exist_ok=True)
        
        # 4. Copy Jar
        dest_jar = os.path.join(server_dir, "server.jar")
        shutil.copy2(source_jar, dest_jar)
        
        # --- FORGE SPECIFIC INSTALLATION ---
        if mod_loader.upper() == "FORGE":
            print(f"INFO: Running Forge Installer for {name}...")
            
            # Check if source jar exists (it might be the installer)
            # If not, try to download strictly if it matches Forge versioning (MC-ForgeVersion)
            # URL format: https://maven.minecraftforge.net/net/minecraftforge/forge/{VERSION}/forge-{VERSION}-installer.jar
            
            installer_name = f"forge-{version}-installer.jar"
            # If the source file was copied as 'server.jar' in step 4, we need to check if it's actually the installer
            # The previous logic copied 'source_jar' to 'server.jar'.
            # If source_jar didn't exist, we might need to download it NOW.
            
            # Since step 1-4 handles copying, let's refine the "source_jar" logic slightly.
            # If we are in create_server, 'server.jar' in destination is what we work with.
            
            # If the copied jar is the installer (which it is for Forge), we run it.
            # If the user provided a version like "1.20.1-47.2.0", we can try download if missing.
            
            # --- Auto-Download Logic ---
            if not os.path.exists(source_jar) and "-" in version:
                print(f"INFO: Installer not found locally. Attempting download for {version}...")
                download_url = f"https://maven.minecraftforge.net/net/minecraftforge/forge/{version}/forge-{version}-installer.jar"
                try:
                    self._download_file(download_url, dest_jar)
                    print(f"INFO: Downloaded Forge Installer {version}")
                except Exception as dl_err:
                     print(f"WARNING: Automatic download failed: {dl_err}. Assuming existing 'server.jar' is correct or will fail.")

            try:
                # 3. Install in text mode
                # java -jar forge-installer.jar --installServer
                install_cmd = ["java", "-jar", "server.jar", "--installServer"]
                
                # Log installation to file for debug
                with open(os.path.join(server_dir, "install.log"), "w") as log_file:
                     subprocess.run(
                        install_cmd, 
                        cwd=server_dir, 
                        check=True, 
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        input=b"\n" 
                    )
                
                print(f"INFO: Forge installation completed for {name}")
                
                # 4. Clean up installer (Optional per guide, but good practice)
                # But 'server.jar' IS the installer in this context. 
                # Rename it to installer.jar.bak or delete?
                # Usually we want to keep the main jar, but for modern forge, the result is libraries + run scripts.
                # The 'server.jar' (installer) is useless after install.
                # However, for Legacy Forge (1.12), the output results in a universal jar.
                
                # Let's check if we have run.bat/run.sh (Modern) or a new jar (Legacy)
                has_run_script = os.path.exists(os.path.join(server_dir, "run.bat")) or os.path.exists(os.path.join(server_dir, "run.sh"))
                
                if has_run_script:
                    # It's modern forge. We can delete the installer (server.jar)
                    # OR rename it to avoid confusion.
                    try:
                        os.remove(dest_jar)
                    except: pass
                else:
                    # It's likely legacy. A new jar 'forge-old-universal.jar' might exist.
                    # We should find it and rename it to 'server.jar' so start() finds it?
                    # Or 'start()' logic should be smart enough.
                    # Start logic looks for 'server.jar' usually. 
                    # If we delete 'server.jar' (installer), we must ensure we have a runnable jar.
                    
                    # Find any other jar
                    jars = [f for f in os.listdir(server_dir) if f.endswith(".jar") and f != "server.jar" and "installer" not in f]
                    if jars:
                        # Found a likely universal jar. Rename it to server.jar? 
                        # Or update database jar_path? 
                        # Keeping 'server.jar' as the standard entry point name is good.
                        os.remove(dest_jar) # Remove installer
                        os.rename(os.path.join(server_dir, jars[0]), dest_jar)
                        print(f"INFO: Legacy Forge detected. Renamed {jars[0]} to server.jar")
                
            except subprocess.CalledProcessError as e:
                print(f"ERROR: Forge installation failed. Check install.log.")
                raise Exception(f"Forge installation failed.")
        
        # 5. Create EULA
        with open(os.path.join(server_dir, "eula.txt"), "w") as f:
            f.write("eula=true\n")
            
        # 6. Create server.properties (basic)
        props = f"""server-port={port}
max-players={max_players}
motd={motd}
online-mode={'true' if online_mode else 'false'}
"""
        with open(os.path.join(server_dir, "server.properties"), "w") as f:
            f.write(props)

        # 7. Create DB Record
        new_server = Server(
            name=name, 
            version=version, 
            ram_mb=ram_mb, 
            port=port,
            online_mode=online_mode, 
            motd=motd,
            mod_loader=mod_loader,
            cpu_cores=cpu_cores,
            disk_mb=disk_mb,
            max_players=max_players,
            disk_usage=jar_size // (1024*1024) # Int MB
        )
        db.add(new_server)
        db.commit()
        db.refresh(new_server)

        instance = MinecraftProcess(
            name=name, ram_mb=ram_mb,
            jar_path=dest_jar,
            working_dir=server_dir,
            server_id=new_server.id
        )
        self.servers[name] = instance
        return new_server

    def delete_server(self, db: Session, name: str):
        instance = self.servers.get(name)
        if instance:
            if instance.is_running():
                print(f"DEBUG: Killing server {name} before deletion")
                instance.kill()
                # Wait for process to fully terminate
                import time
                time.sleep(2)
            del self.servers[name]
        
        record = db.query(Server).filter(Server.name == name).first()
        if record:
            db.delete(record)
            db.commit()
            
        import shutil
        import time
        server_dir = os.path.join(self.base_dir, name)
        if os.path.exists(server_dir):
            # Retry logic for Windows file locks
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    shutil.rmtree(server_dir)
                    print(f"INFO: Successfully deleted server directory: {server_dir}")
                    break
                except PermissionError as e:
                    if attempt < max_retries - 1:
                        print(f"WARNING: Directory locked, retrying in 1s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(1)
                    else:
                        print(f"ERROR: Failed to delete directory {server_dir} after {max_retries} attempts: {e}")
                        raise Exception(f"Could not delete server files. Files may be in use. Please close any applications accessing the server directory and try again.")
                except Exception as e:
                    print(f"ERROR: Unexpected error deleting directory {server_dir}: {e}")
                    raise

    def is_port_free(self, port: int) -> bool:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) != 0

    def _download_file(self, url: str, dest: str):
        import urllib.request
        print(f"DEBUG: Downloading {url} to {dest}")
        with urllib.request.urlopen(url) as response, open(dest, 'wb') as out_file:
            if response.status != 200:
                raise Exception(f"HTTP Status {response.status}")
            import shutil
            shutil.copyfileobj(response, out_file)
    
    async def export_server(self, db: Session, name: str) -> str:
        """Export a server as a ZIP file, excluding logs and temporary files"""
        import zipfile
        import tempfile
        
        # Check if server exists in DB
        server = db.query(Server).filter(Server.name == name).first()
        if not server:
            raise FileNotFoundError(f"Server '{name}' not found")
        
        server_dir = os.path.join(self.base_dir, name)
        if not os.path.exists(server_dir):
            raise FileNotFoundError(f"Server directory not found: {server_dir}")
        
        # Create temp ZIP file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip', prefix=f'{name}_')
        
        try:
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(server_dir):
                    # Skip logs, cache, and temp files
                    dirs[:] = [d for d in dirs if d not in ['logs', 'cache', '__pycache__']]
                    
                    for file in files:
                        if file.endswith(('.pid', '.log')):
                            continue
                        
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, server_dir)
                        zipf.write(file_path, arcname)
            
            print(f"INFO: Server '{name}' exported to {temp_zip.name}")
            return temp_zip.name
        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_zip.name):
                os.remove(temp_zip.name)
            raise
    
    async def import_server(self, db: Session, file):
        """Import a server from a ZIP file"""
        import zipfile
        import tempfile
        import shutil
        
        # Create temp directory for extraction
        temp_dir = tempfile.mkdtemp(prefix='mc_import_')
        
        try:
            # Save uploaded file to temp location
            temp_zip_path = os.path.join(temp_dir, 'server.zip')
            with open(temp_zip_path, 'wb') as f:
                content = await file.read()
                f.write(content)
            
            # Extract ZIP
            extract_dir = os.path.join(temp_dir, 'extracted')
            with zipfile.ZipFile(temp_zip_path, 'r') as zipf:
                zipf.extractall(extract_dir)
            
            # Validate server structure
            if not os.path.exists(os.path.join(extract_dir, 'server.jar')) and \
               not os.path.exists(os.path.join(extract_dir, 'server.properties')):
                raise ValueError("Invalid server ZIP: missing server.jar or server.properties")
            
            # Parse server.properties for metadata
            props_path = os.path.join(extract_dir, 'server.properties')
            server_name = file.filename.replace('.zip', '').replace(' ', '_')
            port = 25565
            max_players = 20
            motd = "Imported Server"
            online_mode = False
            
            if os.path.exists(props_path):
                with open(props_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('server-port='):
                            try:
                                port = int(line.split('=')[1])
                            except: pass
                        elif line.startswith('max-players='):
                            try:
                                max_players = int(line.split('=')[1])
                            except: pass
                        elif line.startswith('motd='):
                            motd = line.split('=', 1)[1] if '=' in line else motd
                        elif line.startswith('online-mode='):
                            online_mode = line.split('=')[1].lower() == 'true'
            
            # Make server name unique if needed
            base_name = server_name
            counter = 1
            while db.query(Server).filter(Server.name == server_name).first():
                server_name = f"{base_name}_{counter}"
                counter += 1
            
            # Move to servers directory
            final_server_dir = os.path.join(self.base_dir, server_name)
            shutil.move(extract_dir, final_server_dir)
            
            # Detect version and mod loader from JAR or properties
            version = "Unknown"
            mod_loader = "VANILLA"
            
            # Try to detect Forge
            if os.path.exists(os.path.join(final_server_dir, 'libraries')):
                mod_loader = "FORGE"
            
            # Get JAR size for disk usage
            jar_path = os.path.join(final_server_dir, 'server.jar')
            disk_usage = 0
            if os.path.exists(jar_path):
                disk_usage = os.path.getsize(jar_path) // (1024 * 1024)
            
            # Create DB record
            new_server = Server(
                name=server_name,
                version=version,
                ram_mb=2048,  # Default
                port=port,
                online_mode=online_mode,
                motd=motd,
                mod_loader=mod_loader,
                cpu_cores=1.0,
                disk_mb=4096,  # Default
                max_players=max_players,
                disk_usage=disk_usage
            )
            db.add(new_server)
            db.commit()
            db.refresh(new_server)
            
            # Create process instance
            instance = MinecraftProcess(
                name=server_name,
                ram_mb=2048,
                jar_path=jar_path,
                working_dir=final_server_dir,
                server_id=new_server.id
            )
            self.servers[server_name] = instance
            
            print(f"INFO: Server '{server_name}' imported successfully")
            return new_server
            
        except Exception as e:
            print(f"ERROR: Import failed: {e}")
            raise
        finally:
            # Cleanup temp directory
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except: pass

server_service = ServerService() # Singleton

