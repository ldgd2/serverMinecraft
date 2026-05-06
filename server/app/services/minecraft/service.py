import os
import shutil
import asyncio
import subprocess
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from database.models import Server
from app.services.minecraft.process import MinecraftProcess

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
            
            # MasterBridge config removed
            masterbridge_config = None
            
            instance = MinecraftProcess(
                name=record.name,
                ram_mb=record.ram_mb,
                jar_path=jar_path,
                working_dir=working_dir,
                port=record.port,
                server_id=record.id,
                masterbridge_config=masterbridge_config,
                cpu_cores=record.cpu_cores
            )
            
            # --- Attempt Recovery ---
            if instance.attempt_recovery():
                # print(f"INFO: Recovered active server {record.name}")
                instance._status = "ONLINE"
                asyncio.create_task(instance._tail_log_file())
                
            self.servers[record.name] = instance

    def get_process(self, name: str) -> MinecraftProcess:
        proc = self.servers.get(name)
        if not proc:
            # Fallback to case-insensitive search
            for sname, sproc in self.servers.items():
                if sname.lower() == name.lower():
                    # print(f"DEBUG: Found process for '{name}' via case-insensitive match: '{sname}'")
                    return sproc
            # print(f"DEBUG: Process not found for '{name}'. Available servers: {list(self.servers.keys())}")
        return proc

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
        motd: str = "A Minecraft Server",
        progress_callback = None
    ):
        if name in self.servers or db.query(Server).filter(Server.name == name).first():
            raise ValueError("Server already exists")
            
        # 0. Port Check & Auto-Assign
        used_ports = [s.port for s in db.query(Server).all()]
        
        import random
        retries = 10
        original_port = port
        while port in used_ports or not self.is_port_free(port):
            port = random.randint(25565, 25600)
            retries -= 1
            if retries <= 0:
                 raise ValueError(f"Could not find a free port. Requested {original_port} was taken.")
                 
        # 1. Create DB Record
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
            status="CREATING"
        )
        db.add(new_server)
        db.commit()
        db.refresh(new_server)

        # 2. Setup Files (Synchronous in this method for backward compatibility)
        self.setup_server_files(db, new_server, progress_callback=progress_callback)
        
        return new_server

    def setup_server_files(self, db: Session, server: Server, progress_callback=None):
        name = server.name
        version = server.version
        mod_loader = server.mod_loader.upper()
        port = server.port
        ram_mb = server.ram_mb
        online_mode = server.online_mode
        disk_mb = server.disk_mb
        max_players = server.max_players
        motd = server.motd

        if progress_callback: progress_callback(10, "Locating version components")

        # 1. Locate Source Jar
        versions_root = os.path.abspath("source/versions")
        if mod_loader == "VANILLA":
            source_jar = os.path.join(versions_root, "vanilla", version, "server.jar")
        else:
            source_jar = os.path.join(versions_root, "modLoader", mod_loader.lower(), version, "server.jar")
            
        if not os.path.exists(source_jar):
            parent_dir = os.path.dirname(source_jar)
            if os.path.exists(parent_dir):
                files = [f for f in os.listdir(parent_dir) if f.endswith(".jar")]
                if files:
                    source_jar = os.path.join(parent_dir, files[0])
                else:
                     raise ValueError(f"Version {version} for {mod_loader} not found (No JAR file).")
            else:
                 raise ValueError(f"Version {version} for {mod_loader} not found.")

        # 2. Check Disk Space
        jar_size = os.path.getsize(source_jar)
        if jar_size > (disk_mb * 1024 * 1024):
             raise ValueError(f"Server JAR exceeds allocated disk space")

        # 3. Create Server Directory
        server_dir = os.path.join(self.base_dir, name)
        os.makedirs(server_dir, exist_ok=True)
        
        if progress_callback: progress_callback(30, "Creating server directory structure")

        # 4. Copy Jar
        dest_jar = os.path.join(server_dir, "server.jar")
        shutil.copy2(source_jar, dest_jar)
        
        if progress_callback: progress_callback(50, "Copying JAR file into place")

        # --- FORGE SPECIFIC INSTALLATION ---
        if mod_loader == "FORGE":
            try:
                install_cmd = ["java", "-jar", "server.jar", "--installServer"]
                with open(os.path.join(server_dir, "install.log"), "w") as log_file:
                     if progress_callback: progress_callback(60, "Running Forge Installer")
                     subprocess.run(install_cmd, cwd=server_dir, check=True, stdout=log_file, stderr=subprocess.STDOUT, input=b"\n")
                
                if progress_callback: progress_callback(80, "Forge installation completed")
                
                # Clean up installer
                has_run_script = os.path.exists(os.path.join(server_dir, "run.bat")) or os.path.exists(os.path.join(server_dir, "run.sh"))
                if has_run_script:
                    try: os.remove(dest_jar)
                    except: pass
                else:
                    jars = [f for f in os.listdir(server_dir) if f.endswith(".jar") and f != "server.jar" and "installer" not in f]
                    if jars:
                        os.remove(dest_jar)
                        os.rename(os.path.join(server_dir, jars[0]), dest_jar)
            except Exception as e:
                raise Exception(f"Forge installation failed: {e}")
        
        # 5. Create EULA
        with open(os.path.join(server_dir, "eula.txt"), "w") as f:
            f.write("eula=true\n")
            
        # 6. Create server.properties
        props = f"server-port={port}\nmax-players={max_players}\nmotd={motd}\nonline-mode={'true' if online_mode else 'false'}\n"
        with open(os.path.join(server_dir, "server.properties"), "w") as f:
            f.write(props)

        if progress_callback: progress_callback(90, "Writing environment configurations")

        # 7. Finalize Record
        server.status = "OFFLINE"
        server.disk_usage = jar_size // (1024*1024)
        db.commit()
        db.refresh(server)

        # 8. Inject Bridge Mod if needed
        if mod_loader != "VANILLA":
            try:
                self.sync_bridge_mod(name)
            except Exception as e:
                print(f"WARNING: Could not sync bridge mod for {name}: {e}")

        # 9. Create Process
        instance = self._create_process(server)
        self.servers[name] = instance
        
        if progress_callback: progress_callback(100, "Server created successfully")
        return server

    def _create_process(self, server_db: Server) -> MinecraftProcess:
        """Create a MinecraftProcess instance from database model"""
        # print(f"DEBUG: _create_process called for server '{server_db.name}'")
        
        # MasterBridge config removed
        masterbridge_config = None
        
        
        process = MinecraftProcess(
            name=server_db.name,
            ram_mb=server_db.ram_mb,
            jar_path=os.path.join(self.base_dir, server_db.name, "server.jar"),
            working_dir=os.path.join(self.base_dir, server_db.name),
            port=server_db.port,
            server_id=server_db.id,
            masterbridge_config=masterbridge_config,
            cpu_cores=server_db.cpu_cores
        )
        
        return process

    def update_process_config(self, name: str, ram_mb: Optional[int] = None, cpu_cores: Optional[float] = None):
        """Update the configuration of an existing process instance"""
        instance = self.servers.get(name)
        if instance:
            if ram_mb is not None:
                instance.ram_mb = ram_mb
            if cpu_cores is not None:
                instance.cpu_cores = cpu_cores
            return True
        return False

    def delete_server(self, db: Session, name: str):
        instance = self.servers.get(name)
        if instance:
            if instance.is_running():
                # print(f"DEBUG: Killing server {name} before deletion")
                instance.kill()
                import time
                time.sleep(2)
            del self.servers[name]
        
        record = db.query(Server).filter(Server.name == name).first()
        if record:
            db.delete(record)
            db.commit()
            
        import time
        server_dir = os.path.join(self.base_dir, name)
        if os.path.exists(server_dir):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    shutil.rmtree(server_dir)
                    # print(f"INFO: Successfully deleted server directory: {server_dir}")
                    break
                except PermissionError as e:
                    if attempt < max_retries - 1:
                        # print(f"WARNING: Directory locked, retrying in 1s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(1)
                    else:
                        # print(f"ERROR: Failed to delete directory {server_dir} after {max_retries} attempts: {e}")
                        raise Exception(f"Could not delete server files. Files may be in use. Please close any applications accessing the server directory and try again.")
                except Exception as e:
                    # print(f"ERROR: Unexpected error deleting directory {server_dir}: {e}")
                    raise

    def sync_bridge_mod(self, server_name: str):
        """Copies the latest modserver binary to the server's mods folder."""
        import json
        
        # 1. Get latest version from versions.json
        v_file = os.path.abspath("static/versions.json")
        if not os.path.exists(v_file):
            return
            
        try:
            with open(v_file, "r") as f:
                data = json.load(f)
            version = data.get("modserver")
            if not version: return
            
            # 2. Source path
            filename = "minebridge-server.jar" # Matching updates.py _PLATFORM_FILE
            src = os.path.abspath(f"static/versions/modserver/{version}/{filename}")
            
            if not os.path.exists(src):
                # Try fallback names if user renamed it
                folder = os.path.dirname(src)
                if os.path.exists(folder):
                    jars = [f for f in os.listdir(folder) if f.endswith(".jar")]
                    if jars: src = os.path.join(folder, jars[0])
                    else: return
                else: return
                
            # 3. Destination path
            mod_dir = os.path.join(self.base_dir, server_name, "mods")
            os.makedirs(mod_dir, exist_ok=True)
            
            # Remove old versions (masterbridge or minebridge)
            for f in os.listdir(mod_dir):
                fl = f.lower()
                if ("minebridge" in fl or "masterbridge" in fl) and f.endswith(".jar"):
                    try: os.remove(os.path.join(mod_dir, f))
                    except: pass
            
            shutil.copy2(src, os.path.join(mod_dir, filename))
            # print(f"INFO: Synced bridge mod to {server_name}")
            
        except Exception as e:
            # print(f"ERROR: Failed to sync bridge mod: {e}")
            raise

    def is_port_free(self, port: int) -> bool:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) != 0

    def _download_file(self, url: str, dest: str):
        import urllib.request
        # print(f"DEBUG: Downloading {url} to {dest}")
        with urllib.request.urlopen(url) as response, open(dest, 'wb') as out_file:
            if response.status != 200:
                raise Exception(f"HTTP Status {response.status}")
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
            
            # print(f"INFO: Server '{name}' exported to {temp_zip.name}")
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
        
        # Create temp directory for extraction
        temp_dir = tempfile.mkdtemp(prefix='mc_import_')
        
        try:
            # Save uploaded file to temp location
            temp_zip_path = os.path.join(temp_dir, 'server.zip')
            with open(temp_zip_path, 'wb') as f:
                while True:
                    chunk = await file.read(1024 * 1024)  # Read 1MB chunks
                    if not chunk:
                        break
                    f.write(chunk)
            
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
                ram_mb=4096,  # Default for 8GB RAM system
                port=port,
                online_mode=online_mode,
                motd=motd,
                mod_loader=mod_loader,
                cpu_cores=6.0,  # Default for 6 core system
                disk_mb=10000,  # Default
                max_players=max_players,
                disk_usage=disk_usage
            )
            db.add(new_server)
            db.commit()
            db.refresh(new_server)
            
            # MasterBridge config removed
            masterbridge_config = None
            
            # Create process instance
            instance = MinecraftProcess(
                name=server_name,
                ram_mb=4096,
                jar_path=jar_path,
                working_dir=final_server_dir,
                port=port,
                masterbridge_config=masterbridge_config
            )
            self.servers[server_name] = instance
            
            # print(f"INFO: Server '{server_name}' imported successfully")
            return new_server
            
        except Exception as e:
            # print(f"ERROR: Import failed: {e}")
            raise
        finally:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except: pass

server_service = ServerService() # Singleton
