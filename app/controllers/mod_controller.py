from fastapi import BackgroundTasks
from app.services.minecraft import server_service
from app.services.mod_service import mod_service
import os

class ModController:
    async def get_versions(self):
        return await mod_service.fetch_versions()

    async def install_server_version(self, server_name: str, version: str, background_tasks: BackgroundTasks):
        server = server_service.get_process(server_name)
        if not server:
            raise ValueError("Server not found")
            
        builds = await mod_service.fetch_builds(version)
        latest_build = builds[-1]
        
        jar_path = server.jar_path
        background_tasks.add_task(mod_service.download_paper_jar, version, latest_build, jar_path)
        
        return {"message": f"Downloading Paper {version} build {latest_build}..."}

    async def search_mods(self, query: str, version: str):
         return await mod_service.search_mods(query, version)

    async def install_mod(self, server_name: str, mod_url: str, background_tasks: BackgroundTasks):
        server = server_service.get_process(server_name)
        if not server:
            raise ValueError("Server not found")
        
        mods_dir = os.path.join(server.working_dir, "mods")
        os.makedirs(mods_dir, exist_ok=True)
        
        filename = mod_url.split("/")[-1]
        if not filename.endswith(".jar"):
            filename += ".jar"
        
        destination = os.path.join(mods_dir, filename)
        background_tasks.add_task(mod_service.install_mod_from_url, mod_url, destination)
        
        return {"message": "Mod installation started"}
