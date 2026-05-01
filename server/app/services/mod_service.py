import os
import shutil
import aiofiles
from fastapi import UploadFile, HTTPException
from typing import List, Dict, Optional
import zipfile
from app.services.server.mod.paper.paper_mod_server import PaperPluginManager
from app.services.server.mod.forge.forge_mod_server import ForgeModManager
from app.services.server.mod.fabric.fabric_mod_server import FabricModManager
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ModService:
    def __init__(self):
        self.servers_dir = os.path.abspath("servers")
        self.paper_manager = PaperPluginManager(base_path=self.servers_dir)
        self.forge_manager = ForgeModManager(base_path=self.servers_dir)
        self.fabric_manager = FabricModManager(base_path=self.servers_dir)
        self.executor = ThreadPoolExecutor(max_workers=3)

    def _get_mods_dir(self, server_name: str) -> str:
        return os.path.join(self.servers_dir, server_name, "mods")

    def ensure_mods_dir(self, server_name: str):
        path = self._get_mods_dir(server_name)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return path

    async def get_installed_mods(self, server_name: str, loader: str = None) -> List[Dict]:
        if loader and loader.upper() == "PAPER":
            # Delegate to PaperPluginManager
            loop = asyncio.get_event_loop()
            try:
                return await loop.run_in_executor(self.executor, self.paper_manager.listar_plugins_instalados, server_name)
            except Exception as e:
                print(f"Error listing Paper plugins: {e}")
                return []
                
        if loader and loader.upper() == "FABRIC":
            loop = asyncio.get_event_loop()
            try:
                return await loop.run_in_executor(self.executor, self.fabric_manager.listar_mods_instalados, server_name)
            except Exception as e:
                print(f"Error listing Fabric mods: {e}")
                return []

        if loader and loader.upper() in ["FORGE", "NEOFORGE", "QUILT"]:
             loop = asyncio.get_event_loop()
             try:
                 return await loop.run_in_executor(self.executor, self.forge_manager.listar_mods_instalados, server_name)
             except Exception as e:
                 print(f"Error listing generic mods: {e}")
                 return []

        mods_dir = self._get_mods_dir(server_name)
        if not os.path.exists(mods_dir):
            return []

        mods = []
        try:
            for f in os.listdir(mods_dir):
                file_path = os.path.join(mods_dir, f)
                stat = os.stat(file_path)
                is_dir = os.path.isdir(file_path)
                
                mods.append({
                    "name": f,
                    "filename": f,
                    "size": stat.st_size if not is_dir else 0,
                    "modified": stat.st_mtime,
                    "is_directory": is_dir,
                    "extension": os.path.splitext(f)[1].lower() if not is_dir else "folder"
                })
        except Exception as e:
            print(f"Error scanning mods directory: {e}")
            
        return mods

    async def rename_mod(self, server_name: str, old_name: str, new_name: str) -> bool:
        mods_dir = self._get_mods_dir(server_name)
        old_path = os.path.join(mods_dir, old_name)
        new_path = os.path.join(mods_dir, new_name)
        
        # Security check: avoid path traversal
        if not old_path.startswith(mods_dir) or not new_path.startswith(mods_dir):
            return False
            
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            return True
        return False

    async def upload_mod(self, server_name: str, file: UploadFile):
        mods_dir = self.ensure_mods_dir(server_name)
        file_path = os.path.join(mods_dir, file.filename)
        
        # Check if it's a zip and user wants to extract (handled by frontend flag?)
        # For now, standard mod upload is keeping the jar/zip as is unless it's a modpack.
        # User said: "puedo arastrar y soltar o seleccionar, en formato zip o rar, lo descomprime y lo guarda en esa carpeta"
        
        temp_path = file_path + ".tmp"
        async with aiofiles.open(temp_path, 'wb') as out_file:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                await out_file.write(chunk)
            
        # Rename to final
        if os.path.exists(file_path):
            os.remove(file_path)
        os.rename(temp_path, file_path)

        # Extraction logic if it's a zip/rar and meant to be extracted
        # Minecraft mods are usually just JARs. If it's a ZIP, it might be a modpack or just a zipped mod.
        # If the user says "lo descomprime", they likely mean if I upload a zip of multiple mods?
        # Let's support auto-extraction if it contains JARs.
        
        if file.filename.endswith(".zip"):
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Check contents
                    file_names = zip_ref.namelist()
                    has_jars = any(f.endswith(".jar") for f in file_names)
                    
                    if has_jars:
                        # Extract all to mods dir
                        zip_ref.extractall(mods_dir)
                        # Remove the zip file after extraction? Maybe keep it as backup or delete.
                        # Usually delete if extracted.
                        os.remove(file_path)
                        return {"message": f"Extracted {len(file_names)} files from {file.filename}"}
            except zipfile.BadZipFile:
                pass # Treat as regular file if bad zip

        return {"message": f"Uploaded {file.filename}"}

    async def delete_mod(self, server_name: str, filename: str, loader: str = None):
        if loader and loader.upper() == "PAPER":
            loop = asyncio.get_event_loop()
            try:
                # Use deep clean method
                success, msg = await loop.run_in_executor(self.executor, self.paper_manager.eliminar_plugin, server_name, filename)
                return success
            except Exception as e:
                print(f"Error deleting Paper plugin: {e}")
                return False
                
        if loader and loader.upper() == "FABRIC":
            loop = asyncio.get_event_loop()
            try:
                success, msg = await loop.run_in_executor(self.executor, self.fabric_manager.eliminar_mod, server_name, filename)
                return success
            except Exception as e:
                 print(f"Error deleting Fabric mod: {e}")
                 return False

        if loader and loader.upper() in ["FORGE", "NEOFORGE", "QUILT"]:
            loop = asyncio.get_event_loop()
            try:
                success, msg = await loop.run_in_executor(self.executor, self.forge_manager.eliminar_mod, server_name, filename)
                return success
            except Exception as e:
                 print(f"Error deleting generic mod: {e}")
                 return False

        mods_dir = self._get_mods_dir(server_name)
        file_path = os.path.join(mods_dir, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    async def search_mods(self, query: str, mc_version: str, loader: str = None) -> List[Dict]:
        import aiohttp
        
        # Map generic loader names to Modrinth facets
        loader_facet = ""
        if loader:
            l = loader.lower()
            if "fabric" in l: loader_facet = '["categories:fabric"]'
            elif "forge" in l: loader_facet = '["categories:forge"]'
            elif "neoforge" in l: loader_facet = '["categories:neoforge"]'
            elif "quilt" in l: loader_facet = '["categories:quilt"]'
        
        facets = f'[["versions:{mc_version}"], ["project_type:mod"]]'
        if loader and loader.upper() == "PAPER":
            # Delegate to PaperPluginManager (Synchronous, so run in executor)
            loop = asyncio.get_event_loop()
            
            # Determine sort type
            # User options: "estrellas", "descargas_recientes", "mas_descargados", "actualizados", "nuevos"
            # We can map standard modrinth sorts or just default to best match
            sort_type = "buscar" if query else "estrellas"
            
            try:
                # 1. Get search URL
                url = await loop.run_in_executor(self.executor, self.paper_manager.obtener_url_categoria, sort_type, query)
                
                # 2. Fetch HTML
                html = await loop.run_in_executor(self.executor, self.paper_manager.obtener_html, url)
                
                # 3. Parse
                raw_results = await loop.run_in_executor(self.executor, self.paper_manager.parsear_lista_resultados, html)
                
                # 4. Map to standardized format
                results = []
                for item in raw_results:
                    # Hangar doesn't give downloads/description in list easily without more parsing
                    # We map 'url' or 'ruta_relativa' to project_id for installation usage
                    results.append({
                        "project_id": item['url'], # Use full URL as ID
                        "title": item['name'],
                        "description": f"Author: {item['author']}",
                        "icon_url": None, # Paper doesn't easily give icons in list without css classes parsing
                        "author": item['author'],
                        "downloads": 0, # Placeholder
                        "loader": "PAPER" # Marker
                    })
                return results
            except Exception as e:
                print(f"Error searching Paper plugins: {e}")
                return []

        if loader and loader.upper() == "FABRIC":
            # Delegate to FabricModManager
            loop = asyncio.get_event_loop()
            sort_type = "relevance"
            if not query: sort_type = "downloads"
            
            try:
                return await loop.run_in_executor(
                    self.executor, 
                    self.fabric_manager.buscar_mods, 
                    query, 
                    mc_version, 
                    sort_type
                )
            except Exception as e:
                print(f"Error searching Fabric mods: {e}")
                return []

        if loader and loader.upper() in ["FORGE", "NEOFORGE", "QUILT"]:
            # Delegate to ForgeModManager (or generic)
            loop = asyncio.get_event_loop()
            sort_type = "relevance"
            if not query: sort_type = "downloads"
            
            try:
                return await loop.run_in_executor(
                    self.executor, 
                    self.forge_manager.buscar_mods, 
                    query, 
                    mc_version, 
                    sort_type, 
                    loader.lower()
                )
            except Exception as e:
                print(f"Error searching generic mods: {e}")
                return []

        # Fallback for old implementations or direct Modrinth calls if needed
        # (The ForgeModManager covers Modrinth logic effectively now)
        return []

    async def install_mod(self, server_name: str, project_id: str, mc_version: str, loader: str) -> bool:
        import aiohttp
        
        if loader and loader.upper() == "PAPER":
             loop = asyncio.get_event_loop()
             try:
                 # project_id holds the URL
                 url = project_id
                 
                 # 1. Fetch details page to get download link
                 html = await loop.run_in_executor(self.executor, self.paper_manager.obtener_html, url)
                 
                 # 2. Parse details
                 mod_data = await loop.run_in_executor(self.executor, self.paper_manager.parsear_detalle_mod, html)
                 
                 # 3. Install
                 success, msg = await loop.run_in_executor(self.executor, self.paper_manager.descargar_e_instalar, mod_data, server_name)
                 
                 if not success:
                     raise Exception(msg)
                 return True
             except Exception as e:
                 raise Exception(f"Failed to install Paper plugin: {e}")

        if loader and loader.upper() == "FABRIC":
             loop = asyncio.get_event_loop()
             try:
                 slug = project_id
                 info = await loop.run_in_executor(
                     self.executor, 
                     self.fabric_manager.obtener_info_descarga, 
                     slug, 
                     mc_version
                 )
                 if not info:
                     raise Exception(f"No compatible installed version found for {mc_version} (FABRIC)")

                 success, msg = await loop.run_in_executor(
                     self.executor, 
                     self.fabric_manager.instalar_mod, 
                     server_name, 
                     info
                 )
                 if not success:
                     raise Exception(msg)
                 return True
             except Exception as e:
                 raise Exception(f"Failed to install Fabric mod: {e}")

        if loader and loader.upper() in ["FORGE", "NEOFORGE", "QUILT"]:
             loop = asyncio.get_event_loop()
             try:
                 slug = project_id
                 info = await loop.run_in_executor(
                     self.executor, 
                     self.forge_manager.obtener_info_descarga, 
                     slug, 
                     mc_version, 
                     loader.lower()
                 )
                 if not info:
                     raise Exception(f"No compatible installed version found for {mc_version} ({loader})")

                 success, msg = await loop.run_in_executor(
                     self.executor, 
                     self.forge_manager.instalar_mod, 
                     server_name, 
                     info
                 )
                 if not success:
                     raise Exception(msg)
                 return True
             except Exception as e:
                 raise Exception(f"Failed to install mod: {e}")

        raise Exception("Unsupported loader or generic fallback not implemented")

mod_service = ModService()
