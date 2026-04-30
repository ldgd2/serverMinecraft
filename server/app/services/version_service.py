import os
import json
import shutil
import requests
import hashlib
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from database.models.version import Version

# Import clients from source endpoints
# Assuming source is a package. if not we might need to fix that or use sys.path
try:
    from source.endpoints.paper.paper import PaperMCClient
    from source.endpoints.fabric.dabric import FabricClient
    from source.endpoints.forge.forge import ForgeClient
    from source.endpoints.vanilla.vanilla import VanillaClient
except ImportError:
    # If standard import fails, we might need to adjust path or it's running in a context where source isn't a package
    import sys
    sys.path.append(os.getcwd())
    from source.endpoints.paper.paper import PaperMCClient
    from source.endpoints.fabric.dabric import FabricClient
    from source.endpoints.forge.forge import ForgeClient
    from source.endpoints.vanilla.vanilla import VanillaClient

class VersionService:
    VERSION_DIR = "source/versions"

    def __init__(self, db: Session):
        self.db = db
        self.paper_client = PaperMCClient()
        self.fabric_client = FabricClient()
        self.forge_client = ForgeClient()
        self.vanilla_client = VanillaClient()

    def get_installed_versions(self) -> List[Version]:
        return self.db.query(Version).filter(Version.downloaded == True).all()

    def get_remote_versions(self, loader_type: str) -> Dict:
        """
        Fetch available versions from remote APIs.
        Returns a simplified list for the UI.
        """
        loader_type = loader_type.upper()
        if loader_type == "PAPER":
            # Paper structure: project -> version -> builds
            # We just want a list of versions for the dropdown
            try:
                project = self.paper_client.get_project_details("paper")
                return {"versions": project.versions[::-1]} # Newest first
            except Exception as e:
                return {"error": str(e)}

        elif loader_type == "FABRIC":
            # Fabric: Game versions
            try:
                games = self.fabric_client.get_game_versions()
                # Filter stable?
                versions = [g.version for g in games if g.stable]
                return {"versions": versions}
            except Exception as e:
                return {"error": str(e)}

        elif loader_type == "FORGE":
            # Forge: Promotions
            try:
                promos = self.forge_client._get_promotions()
                # Extract unique MC versions from promos
                # The promos dict keys are like "1.20.1-recommended"
                mc_versions = set()
                for key in promos.promos.keys():
                    if "-" in key:
                        mc_ver = key.split("-")[0]
                        mc_versions.add(mc_ver)
                # Sort versions (rough sort)
                sorted_vers = sorted(list(mc_versions), reverse=True) 
                return {"versions": sorted_vers}
            except Exception as e:
                return {"error": str(e)}
        
        elif loader_type == "VANILLA":
            try:
                manifest = self.vanilla_client._get_manifest()
                # releases only for now
                versions = [v.id for v in manifest.versions if v.type == 'release']
                return {"versions": versions}
            except Exception as e:
                return {"error": str(e)}

        return {"error": "Unknown loader type"}

    def get_version_stats(self) -> Dict:
        """
        Returns counts of installed versions by type.
        """
        stats = {
            "total": 0,
            "vanilla": 0,
            "paper": 0,
            "forge": 0,
            "fabric": 0
        }
        
        versions = self.get_installed_versions()
        stats["total"] = len(versions)
        
        for v in versions:
            l_type = v.loader_type.lower()
            if l_type in stats:
                stats[l_type] += 1
                
        return stats

    def download_version(self, loader_type: str, mc_version: str, loader_version_id: str = "latest", progress_callback=None) -> Version:
        """
        Downloads the server jar and saves it to source/versions/{type}/{mc_ver}/...
        """
        loader_type = loader_type.upper()
        
        # 1. Get Download Info (JSON)
        download_info_json = "{}"
        if loader_type == "PAPER":
            # Paper uses build_id as loader_version_id
            download_info_json = self.paper_client.obtener_datos_descarga("paper", mc_version, loader_version_id)
        elif loader_type == "FABRIC":
            download_info_json = self.fabric_client.obtener_datos_descarga(mc_version, "latest", "latest")
        elif loader_type == "FORGE":
            download_info_json = self.forge_client.obtener_datos_descarga(mc_version, "recommended")
        elif loader_type == "VANILLA":
            download_info_json = self.vanilla_client.obtener_datos_descarga(mc_version)
        
        data = json.loads(download_info_json)
        if "error" in data:
            raise Exception(data["error"])

        # 2. Extract Data
        download_url = data.get("download_url")
        filename = data.get("filename")
        sha256 = data.get("sha256") or data.get("sha1") # Vanilla uses sha1
        
        if not download_url or not filename:
            raise Exception("Incomplete download data received")

        # 3. Prepare Paths
        # Structure: 
        #   source/versions/vanilla/1.20.1/server.jar
        #   source/versions/modLoader/forge/1.20.1/server.jar
        
        if loader_type == "VANILLA":
            # Direct path for vanilla
            base_path = os.path.join(self.VERSION_DIR, "vanilla", mc_version)
        else:
            # Subfolder for modLoader
            base_path = os.path.join(self.VERSION_DIR, "modLoader", loader_type.lower(), mc_version)
            
        os.makedirs(base_path, exist_ok=True)
        file_path = os.path.join(base_path, filename)

        # 4. Download
        total_size = 0
        try:
            head_resp = requests.head(download_url, timeout=5)
            total_size = int(head_resp.headers.get('content-length', 0))
        except Exception:
            pass

        file_exists = os.path.exists(file_path)
        current_file_size = os.path.getsize(file_path) if file_exists else 0

        # Download if file doesn't exist, is empty, or size doesn't match total_size
        if not file_exists or current_file_size == 0 or (total_size > 0 and current_file_size != total_size):
            downloaded_size = 0
            import time
            start_time = time.time()
            
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if progress_callback and total_size > 0:
                            percent = int((downloaded_size / total_size) * 100)
                            elapsed = time.time() - start_time
                            speed = downloaded_size / elapsed if elapsed > 0 else 0 # bytes/sec
                            eta = (total_size - downloaded_size) / speed if speed > 0 else 0
                            progress_callback(percent, downloaded_size, total_size, speed, eta)
        else:
            if progress_callback and total_size > 0:
                progress_callback(100, total_size, total_size, 0, 0)
        
        # 5. Get File Stats
        file_size = os.path.getsize(file_path)
        
        # 6. Save to DB
        # Check if exists
        existing = self.db.query(Version).filter(
            Version.loader_type == loader_type,
            Version.mc_version == mc_version,
            Version.loader_version == str(data.get("build") or data.get("type") or "latest")
            # This unique constraint logic might need refinement based on exact versioning
        ).first()

        version_record = existing or Version()
        version_record.loader_type = loader_type
        version_record.mc_version = mc_version
        version_record.loader_version = str(data.get("build") or data.get("loader_version") or data.get("forge_version") or "latest")
        version_record.name = f"{loader_type} {mc_version} ({version_record.loader_version})"
        version_record.local_path = file_path
        version_record.file_size = file_size
        version_record.sha256 = sha256
        version_record.url = download_url
        version_record.downloaded = True
        
        if not existing:
            self.db.add(version_record)
        
        self.db.commit()
        self.db.refresh(version_record)
        
        return version_record
