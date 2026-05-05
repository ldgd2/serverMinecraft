import asyncio
import os
import psutil
import subprocess
import re
import json
from typing import Dict, Optional, List
from datetime import datetime
from asyncio import subprocess as async_subprocess
from app.services.minecraft.player_manager import PlayerManager
from app.services.minecraft.player_stats_syncer import PlayerStatsSyncer
from database.connection import SessionLocal
from core.broadcaster import broadcaster

class MinecraftProcess:
    def __init__(self, name: str, ram_mb: int, jar_path: str, working_dir: str, server_id: int = None, masterbridge_config: Dict = None, cpu_cores: float = 1.0):
        self.name = name
        self.server_id = server_id
        self.ram_mb = ram_mb
        self.cpu_cores = cpu_cores
        self.jar_path = jar_path
        self.working_dir = working_dir
        self.process: Optional[async_subprocess.Process] = None
        self.log_subscribers: List[asyncio.Queue] = []
        self._status = "OFFLINE" # OFFLINE, STARTING, ONLINE, STOPPING
        self.current_players = 0
        self.player_manager = PlayerManager(server_name=name)
        self.recent_activity = [] # List of {type, user, reason, time}
        self._last_stats_time = 0
        self._last_stats = None
        
        # MasterBridge integration removed
        
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
        
        # --- CLEANUP SESSION LOCK ---
        # Minecraft creates a session.lock file in the world folder. 
        # If the server crashes, this file might remain and prevent restart.
        lock_file = os.path.join(self.working_dir, "world", "session.lock")
        if os.path.exists(lock_file):
            try:
                print(f"INFO: Found stale session.lock for {self.name}, removing...")
                os.remove(lock_file)
            except Exception as e:
                print(f"WARN: Could not remove session.lock: {e}")

        print(f"DEBUG: Working dir: {self.working_dir}")
        print(f"DEBUG: Jar path: {self.jar_path}")
        self._status = "STARTING"

        # Rotate latest.log to prevent reading old "Stopping" status
        log_file = os.path.join(self.working_dir, "logs", "latest.log")
        if os.path.exists(log_file):
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
                backup = os.path.join(self.working_dir, "logs", f"latest-{timestamp}.log")
                os.rename(log_file, backup)
                print(f"INFO: Rotated old latest.log to {os.path.basename(backup)}")
            except Exception as e:
                print(f"WARN: Failed to rotate latest.log: {e}")

        # --- FORGE STARTUP LOGIC ---
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
            
            # Append new memory args and Aikar's flags for optimal garbage collection
            new_lines.append(f"\n-Xmx{self.ram_mb}M\n")
            new_lines.append(f"-Xms{self.ram_mb}M\n")
            
            # Aikar's flags optimized for 6GB RAM / 6 Cores
            aikar_flags = [
                "-XX:+UseG1GC",
                "-XX:+ParallelRefProcEnabled",
                "-XX:MaxGCPauseMillis=200",
                "-XX:+UnlockExperimentalVMOptions",
                "-XX:+DisableExplicitGC",
                "-XX:G1NewSizePercent=30",
                "-XX:G1MaxNewSizePercent=40",
                "-XX:G1HeapRegionSize=16M",
                "-XX:G1ReservePercent=20",
                "-XX:G1HeapWastePercent=5",
                "-XX:G1MixedGCCountTarget=4",
                "-XX:InitiatingHeapOccupancyPercent=15",
                "-XX:G1MixedGCLiveThresholdPercent=35",
                "-XX:G1RSetUpdatingPauseTimePercent=5",
                "-XX:SurvivorRatio=32",
                "-XX:+PerfDisableSharedMem",
                "-XX:MaxTenuringThreshold=1",
                "-Dusing.aikars.flags=https://mcflags.emc.gs",
                "-Daikars.new.flags=true"
            ]
            for flag in aikar_flags:
                new_lines.append(f"{flag}\n")
            
            with open(args_file, "w") as f:
                f.writelines(new_lines)
                
            # --- Construct Command ---
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
                 print("DEBUG: Modern Forge detected but args file not found. Trying standard JAR start as fallback.")
                 is_modern_forge = False # Fallback to jar
        else:
             is_modern_forge = False

        if not is_modern_forge:
             cmd = [
                "java",
                f"-Xmx{self.ram_mb}M",
                f"-Xms{self.ram_mb}M",
                "-XX:+UseG1GC",
                "-XX:+ParallelRefProcEnabled",
                "-XX:MaxGCPauseMillis=200",
                "-XX:+UnlockExperimentalVMOptions",
                "-XX:+DisableExplicitGC",
                "-XX:G1NewSizePercent=30",
                "-XX:G1MaxNewSizePercent=40",
                "-XX:G1HeapRegionSize=8M",
                "-XX:G1ReservePercent=20",
                "-XX:G1HeapWastePercent=5",
                "-XX:G1MixedGCCountTarget=4",
                "-XX:InitiatingHeapOccupancyPercent=15",
                "-XX:G1MixedGCLiveThresholdPercent=90",
                "-XX:G1RSetUpdatingPauseTimePercent=5",
                "-XX:SurvivorRatio=32",
                "-XX:+PerfDisableSharedMem",
                "-XX:MaxTenuringThreshold=1",
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
            
            # --- Set CPU Affinity ---
            try:
                p = psutil.Process(self.process.pid)
                # On Windows/Linux we can try to set affinity. 
                # cpu_cores is a float, so we take ceil or just a range.
                # If cpu_cores >= total, we use all.
                total_cpus = psutil.cpu_count()
                cores_to_use = min(total_cpus, max(1, int(self.cpu_cores)))
                p.cpu_affinity(list(range(cores_to_use)))
                print(f"INFO: Set CPU affinity for {self.name} to {cores_to_use} cores")
            except Exception as e:
                print(f"WARN: Failed to set CPU affinity: {e}")
            
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
                    self._wait_for_pid_exit(timeout=10.0)
            except asyncio.TimeoutError:
                print(f"WARN: Server {self.name} didn't stop gracefully, killing...")
                self.kill()
                
            self._status = "OFFLINE"
            self.current_players = 0
            print(f"INFO: Server {self.name} stopped successfully - status set to OFFLINE")
        except Exception as e:
            print(f"ERROR: Error stopping server {self.name}: {e}")
            self.kill()  # Force kill on error
            
    def _wait_for_pid_exit(self, timeout=10.0):
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
        pid_file = os.path.join(self.working_dir, "server.pid")
        if os.path.exists(pid_file):
            try:
                with open(pid_file, "r") as f:
                    return int(f.read().strip())
            except: pass
        return None

    async def write(self, command: str):
        # Limpiar comando (quitar / inicial si lo tiene)
        command = command.lstrip('/')
        
        # 1. Intentar por STDIN (el método más rápido)
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(f"{command}\n".encode())
                await self.process.stdin.drain()
                return True
            except Exception as e:
                print(f"WARN: Falló STDIN para {self.name}: {e}")
        
        # 2. Fallback: Intentar por RCON (indispensable si el proceso fue recuperado o el pipe se rompió)
        try:
            from app.services.minecraft.rcon import _RconClient
            import os
            # Priorizar RCON del servidor específico si estuviera configurado, si no, usar variables de entorno
            host = os.getenv("RCON_HOST", "127.0.0.1")
            port = int(os.getenv("RCON_PORT", "25575"))
            password = os.getenv("RCON_PASSWORD", "")
            
            if password:
                # Usar un timeout corto para no bloquear el hilo
                client = _RconClient(host, port, password)
                client.send(command)
                return True
        except Exception:
            pass
            
        msg = f"ERROR: No se pudo enviar comando a {self.name} (STDIN y RCON fallaron)."
        print(msg)
        for q in self.log_subscribers:
            await q.put(f"[MANAGER] {msg}")
        return False


    def _add_activity(self, type: str, user: str, reason: str = None, timestamp: str = None):
         if not hasattr(self, 'recent_activity'): self.recent_activity = []
         
         if not timestamp:
             timestamp = datetime.now().isoformat()
         
         is_dup = False
         for item in self.recent_activity[:10]: # Check last 10
             if item['type'] == type and item['user'] == user and item['timestamp'] == timestamp:
                 is_dup = True
                 break
         
         if is_dup: return

         log_file = os.path.join(self.working_dir, "logs", "user_connections.log")
         try:
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
         if len(self.recent_activity) > 50:
             self.recent_activity.pop()
    
    # --- Player Management Methods ---
    def get_online_players(self):
        # 1. Obtener lista del Bridge (Mod)
        bridge_players = {}
        try:
            from routes.bridge import server_player_cache
            cached = server_player_cache.get(self.name)
            if cached:
                bridge_players = cached
        except Exception: pass
            
        # 2. Obtener lista de los Logs (Fallback/Detector de inconsistencias)
        log_players = self.player_manager.get_players() # Devuelve lista de dicts
        
        # 3. Fusionar (El Bridge manda, pero los Logs confirman si alguien falta)
        final_players = []
        seen_names = set()
        
        # Meter primero los del Bridge (tienen más info: IP, skin, etc)
        for name, data in bridge_players.items():
            final_players.append({"username": name, **data})
            seen_names.add(name.lower())
            
        # Añadir los que están en logs pero no en bridge
        for p in log_players:
            if p['username'].lower() not in seen_names:
                final_players.append(p)
                seen_names.add(p['username'].lower())
        
        return final_players
    
    async def kick_player(self, username: str):
        if not self.is_running() or self._status != "ONLINE":
            return False
            
        pass

        await self.write(f"kick {username}")
        print(f"INFO: Kicked player {username} from {self.name}")
        return True
    
    async def ban_user(self, username: str, reason: str = "Banned by admin", expires: str = "forever"):
        if not self.is_running() or self._status != "ONLINE":
            return False
            
        pass
        
        await self.write(f"ban {username} {reason}")
        
        ban_file = os.path.join(self.working_dir, "banned-players.json")
        bans = []
        if os.path.exists(ban_file):
            try:
                with open(ban_file, 'r') as f:
                    bans = json.load(f)
            except: pass
        
        bans = [b for b in bans if b.get('name') != username]
        
        uuid = self.player_manager.online_players.get(username, {}).get('uuid', 'unknown')
        
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
            await self.write("banlist reload") 
        except Exception as e:
            print(f"ERROR: Could not write ban file: {e}")
            
        print(f"INFO: Banned user {username} from {self.name}")
        return True

    async def update_ban(self, username: str, reason: str = None, expires: str = None):
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
                return True
        except Exception as e:
            print(f"ERROR: Failed to update ban: {e}")
        return False
    
    async def ban_ip(self, ip: str, reason: str = "Banned by admin", username: str = None):
        if not self.is_running() or self._status != "ONLINE":
            return False
        
        await self.write(f"ban-ip {ip} {reason}")
        
        ban_file = os.path.join(self.working_dir, "banned-ips.json")
        bans = []
        if os.path.exists(ban_file):
            try:
                with open(ban_file, 'r') as f:
                    bans = json.load(f)
            except: pass
        
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
                record["name"] = username 
                
            bans.append(record)
            with open(ban_file, 'w') as f:
                json.dump(bans, f, indent=2)
        
        print(f"INFO: Banned IP {ip} from {self.name}")
        return True
    
    def get_bans(self):
        players = []
        ips = []
        
        player_ban_file = os.path.join(self.working_dir, "banned-players.json")
        if os.path.exists(player_ban_file):
            try:
                with open(player_ban_file, 'r') as f:
                    players = json.load(f)
            except: pass
        
        ip_ban_file = os.path.join(self.working_dir, "banned-ips.json")
        if os.path.exists(ip_ban_file):
            try:
                with open(ip_ban_file, 'r') as f:
                    ips = json.load(f)
            except: pass
        
        return {"players": players, "ips": ips}
    
    async def unban_user(self, username: str):
        pass

        # Run command if online
        if self.is_running() and self._status == "ONLINE":
            await self.write(f"pardon {username}")
        
        # Always try to update file
        ban_file = os.path.join(self.working_dir, "banned-players.json")
        if os.path.exists(ban_file):
            try:
                bans = []
                with open(ban_file, 'r', encoding='utf-8') as f:
                    bans = json.load(f)
                
                # Filter out the user
                initial_count = len(bans)
                bans = [b for b in bans if b.get('name') != username]
                
                if len(bans) < initial_count:
                    with open(ban_file, 'w', encoding='utf-8') as f:
                        json.dump(bans, f, indent=2)
            except Exception as e:
                print(f"ERROR: Could not update ban file: {e}")
        
        print(f"INFO: Unbanned user {username} from {self.name}")
        return True
    
    async def unban_ip(self, ip: str):
        if self.is_running() and self._status == "ONLINE":
            await self.write(f"pardon-ip {ip}")
        
        ban_file = os.path.join(self.working_dir, "banned-ips.json")
        if os.path.exists(ban_file):
            try:
                bans = []
                with open(ban_file, 'r', encoding='utf-8') as f:
                    bans = json.load(f)
                
                bans = [b for b in bans if b.get('ip') != ip]
                
                with open(ban_file, 'w', encoding='utf-8') as f:
                    json.dump(bans, f, indent=2)
            except Exception as e:
                print(f"ERROR: Could not update ban file: {e}")
        
        print(f"INFO: Unbanned IP {ip} from {self.name}")
        return True

    async def op_player(self, username: str):
        if not self.is_running() or self._status != "ONLINE":
            return False
        await self.write(f"op {username}")
        print(f"INFO: Opped player {username} on {self.name}")
        return True

    async def deop_player(self, username: str):
        if not self.is_running() or self._status != "ONLINE":
            return False
        await self.write(f"deop {username}")
        print(f"INFO: De-opped player {username} on {self.name}")
        return True
    
    # --- Teleportation Methods ---
    async def tp_player_to_player(self, username: str, target_username: str):
        if not self.is_running() or self._status != "ONLINE":
            return False
        await self.write(f"tp {username} {target_username}")
        print(f"INFO: Teleported {username} to {target_username} on {self.name}")
        return True

    async def tp_player_to_coords(self, username: str, x: Any, y: Any, z: Any):
        if not self.is_running() or self.status == "OFFLINE":
            return False
        
        try:
            # Asegurar que las coordenadas sean numéricas y redondeadas para evitar errores de sintaxis
            fx, fy, fz = float(x), float(y), float(z)
            # Minecraft usa espacio como separador
            await self.write(f"tp {username} {fx:.2f} {fy:.2f} {fz:.2f}")
            print(f"INFO: Teleported {username} to {fx:.2f} {fy:.2f} {fz:.2f} on {self.name}")
            return True
        except Exception as e:
            print(f"ERROR: Invalid TP coordinates for {username}: {x}, {y}, {z} - {e}")
            return False

    async def tp_players_to_player(self, players: List[str], target_username: str):
        if not self.is_running() or self.status == "OFFLINE":
            return False
        
        # Si la lista está vacía o contiene '@a', usamos '@a' para eficiencia
        if not players or "@a" in players:
            await self.write(f"tp @a {target_username}")
            print(f"INFO: Teleported everyone to {target_username} on {self.name}")
        else:
            for player in players:
                # Evitar TP a sí mismo (para no saturar la consola)
                if player.lower() != target_username.lower():
                    await self.write(f"tp {player} {target_username}")
            print(f"INFO: Teleported {len(players)} players to {target_username} on {self.name}")
        return True
    
    # --- MasterBridge Event Triggers Removed ---

    def is_process_alive(self):
        pid = self._get_pid()
        if not pid: return False
        return psutil.pid_exists(pid)

    def is_running(self):
        return self.is_process_alive()

    # --- Log Parsing Delegate ---
    def _parse_line_event(self, line: str, default_date: str = None):
        # Determine if we should update state from logs.
        # If the Mod is already pushing data to the Bridge, we avoid updating from logs 
        # to prevent duplicates and save CPU.
        update_state = (default_date is None)
        
        # Check if bridge has data. If it does, we assume Mod is active and skip log updates.
        if update_state and self.player_manager.online_players:
             # There is data in the cache (likely from Bridge).
             # We still parse for activity logging but we don't update state.
             update_state = False
             
        event = self.player_manager.parse_log_line(line, update_state=update_state)
        
        if event:
            if update_state:
                self.current_players = self.player_manager.get_count()
                
            if event.get('timestamp'):
                 if default_date:
                     event['timestamp'] = f"{default_date}T{event['timestamp']}"
                 elif 'T' not in event['timestamp']:
                     event['timestamp'] = f"{datetime.now().strftime('%Y-%m-%d')}T{event['timestamp']}"
            return event
        return None

    def _initialize_history_file(self, target_file):
        import gzip
        import glob
        
        log_dir = os.path.join(self.working_dir, "logs")
        if not os.path.exists(log_dir): return
        
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        
        gz_files = glob.glob(os.path.join(log_dir, "*.log.gz"))
        gz_files.sort(key=os.path.getmtime, reverse=True)
        gz_to_read = gz_files[:10]
        
        events = []
        
        for gz_file in reversed(gz_to_read):
            try:
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

        latest_log = os.path.join(log_dir, "latest.log")
        if os.path.exists(latest_log):
             try:
                date_part = datetime.fromtimestamp(os.path.getmtime(latest_log)).strftime('%Y-%m-%d')
                with open(latest_log, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        event = self._parse_line_event(line, default_date=date_part)
                        if event:
                            events.append(event)
             except Exception as e:
                 print(f"WARN: Failed to process latest.log for history: {e}")
                
        try:
            with open(target_file, "w", encoding="utf-8") as f:
                for e in events:
                    f.write(f"{e.get('timestamp')} | {e.get('type')} | {e.get('user')} | {e.get('reason')}\n")
        except Exception as e:
            print(f"ERROR: Could not write history file: {e}")

    def load_activity_history(self):
        log_file = os.path.join(self.working_dir, "logs", "user_connections.log")
        if not os.path.exists(log_file):
            self._initialize_history_file(log_file)
            
        if os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
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
        
        retries = 20
        while not os.path.exists(log_file_path) and retries > 0:
            await asyncio.sleep(0.5)
            retries -= 1
            
        if not os.path.exists(log_file_path):
             print(f"WARNING: Log file not found for {self.name}")
             return

        try:
            with open(log_file_path, "r", encoding='utf-8', errors='replace') as f:
                # Always start from beginning since we rotated the log
                f.seek(0)
                
                while self.is_running():
                    line = f.readline()
                    
                    if not self.is_running():
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
                    
                    # FAST-PATH: Ignorar warnings de carga y movimiento para no saturar el procesador
                    if "Can't keep up!" in cleaned_line or "moved too quickly!" in cleaned_line or "Mismatch in destroy block pos" in cleaned_line:
                        continue

                    print(f"[{self.name}] {cleaned_line}")
                    
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
                    elif "Loading Minecraft" in cleaned_line or "Loading Forge" in cleaned_line or "Loading 44 mods" in cleaned_line:
                        self._status = "LOADING"
                        print(f"INFO: Server {self.name} is now LOADING resources")
                    elif "Preparing level" in cleaned_line or "Preparing spawn area" in cleaned_line:
                        self._status = "PREPARING"
                        print(f"INFO: Server {self.name} is now PREPARING world")
                    elif "FAILED TO BIND TO PORT" in cleaned_line or "Address already in use" in cleaned_line:
                        self._status = "ERROR (Port Blocked)"
                        print(f"ERROR: Server {self.name} failed to bind port!")
                    elif "Encountered an unexpected exception" in cleaned_line or "Failed to initialize server" in cleaned_line:
                        self._status = "ERROR (Crash)"
                        print(f"ERROR: Server {self.name} crashed during startup!")
                    
                    event = self._parse_line_event(cleaned_line)
                    if event:
                        self._add_activity(event['type'], event['user'], event.get('reason'), event.get('timestamp'))
                        
                        # Sync stats if player leaves or is kicked
                        if event['type'] in ['leave', 'kick'] and self.server_id:
                            username = event['user']
                            # Get UUID from event
                            uuid = event.get('uuid')
                            if uuid and uuid != 'unknown':
                                try:
                                    db = SessionLocal()
                                    syncer = PlayerStatsSyncer(self.working_dir, self.server_id)
                                    syncer.sync_player_stats(db, uuid)
                                    db.close()
                                    print(f"INFO: Synced stats for {username} ({uuid}) on {self.name}")
                                except Exception as e:
                                    print(f"ERROR: Failed to sync stats for {username}: {e}")

                        # Log-based Broadcast disabled to avoid duplicates (Mod bridge handles this better)
                        # chat_msg = cleaned_line.split("INFO]: ")[1] if "INFO]: " in cleaned_line else cleaned_line
                        # chat_type = "join" if event['type'] == 'join' else "leave"
                        # if event['type'] == 'kick': chat_type = "leave"
                        # 
                        # asyncio.create_task(broadcaster.broadcast_chat(
                        #     self.name, 
                        #     "System", 
                        #     chat_msg, 
                        #     is_system=True, 
                        #     chat_type=chat_type
                        # ))
                        pass
                    
                    # Also broadcast raw console chat if detected (fallback for when mod is not sending events)
                    # elif "]: <" in cleaned_line:
                    #     try:
                    #         parts = cleaned_line.split("]: <", 1)
                    #         if len(parts) > 1:
                    #             sender_part, message = parts[1].split("> ", 1)
                    #             asyncio.create_task(broadcaster.broadcast_chat(
                    #                 self.name,
                    #                 sender_part,
                    #                 message,
                    #                 is_system=False,
                    #                 chat_type="received"
                    #             ))
                    #     except: pass

                    # Always broadcast to console subscribers
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
        import time
        current_time = time.time()
        if self._last_stats and (current_time - self._last_stats_time) < 2.5:
            return self._last_stats

        pid = self._get_pid()
        
        if not pid or not psutil.pid_exists(pid):
            self._status = "OFFLINE"
            return {"status": "OFFLINE", "cpu": 0, "ram": 0, "players": 0}
        
        log_file = os.path.join(self.working_dir, "logs", "latest.log")
        status_from_log = "STARTING"  
        players_from_log = 0
        
        if not self.process and os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(0, os.SEEK_END)
                    file_size = f.tell()
                    # Read more of log for player tracking (last 50KB)
                    f.seek(max(0, file_size - 50000))
                    tail = f.read()
                    
                    lines = tail.strip().split('\n')
                    
                    has_done = False
                    has_stopping = False
                    has_terminated = False
                    
                    # Track players if player_manager is empty (recovery mode)
                    temp_online = set()
                    
                    for line in lines:
                        if "Done (" in line or "Done preparing level" in line:
                            has_done = True
                        if "Stopping server" in line or "Stopping the server" in line:
                            has_stopping = True
                        if "Awaiting termination" in line or "All RegionFile I/O tasks to complete" in line:
                            has_terminated = True
                        
                        # Parse player join/leave from log
                        if " joined the game" in line:
                            match = re.search(r':\s*(\S+)\s+joined the game', line)
                            if match:
                                temp_online.add(match.group(1))
                        if " left the game" in line or " lost connection:" in line:
                            match = re.search(r':\s*(\S+)\s+(?:left the game|lost connection)', line)
                            if match:
                                temp_online.discard(match.group(1))
                    
                    if has_terminated or has_stopping:
                        status_from_log = "STOPPING"
                        if has_terminated:  
                            self._status = "OFFLINE"
                            return {"status": "OFFLINE", "cpu": 0, "ram": 0, "players": 0}
                    elif has_done:
                        status_from_log = "ONLINE"
                    elif "Preparing level" in tail or "Preparing start region" in tail:
                        status_from_log = "PREPARING"
                    elif "Loading Minecraft" in tail:
                        status_from_log = "LOADING"
                    else:
                        status_from_log = "STARTING"
                    
                    self._status = status_from_log
                    
                    # Use temp count if player_manager is empty (orphan recovery)
                    if self.player_manager.get_count() == 0 and len(temp_online) > 0:
                        players_from_log = len(temp_online)
                        # Sync to player_manager for consistent API response
                        for p in temp_online:
                            # Use add_player for thread safety
                            self.player_manager.add_player(p, {'joined_at': datetime.now().isoformat(), 'uuid': 'unknown'})
                        
            except Exception as e:
                print(f"ERROR: Could not read log file for {self.name}: {e}")
        
        try:
            sys_proc = psutil.Process(pid)
            with sys_proc.oneshot():
                cpu = sys_proc.cpu_percent()
                mem = int(sys_proc.memory_info().rss / (1024 * 1024))
            
            # Use player_manager count, or recovered count from log
            player_count = self.current_players
            if player_count == 0 and players_from_log > 0:
                player_count = players_from_log
                self.current_players = players_from_log  # Update for next call
            
            stats = {"status": self.status, "cpu": cpu, "ram": mem, "players": player_count, "recent_activity": getattr(self, 'recent_activity', [])}
            
            # Merge MasterBridge data if available
            # (Removed)

            
            self._last_stats = stats
            self._last_stats_time = current_time
            return stats
        except psutil.NoSuchProcess:
            self._status = "OFFLINE"
            stats = {"status": "OFFLINE", "cpu": 0, "ram": 0, "players": 0}
            self._last_stats = stats
            self._last_stats_time = current_time
            return stats

    def _find_pid_by_scanning(self):
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
        pid = self._get_pid()
        
        if not pid:
            pid = self._find_pid_by_scanning()
            if pid:
                print(f"DEBUG: Found orphaned server process {pid} for {self.name}")
                try:
                    with open(os.path.join(self.working_dir, "server.pid"), "w") as f:
                        f.write(str(pid))
                except: pass
                
        if pid and psutil.pid_exists(pid):
            return True
        
        if pid: self._cleanup_pid()
        return False
