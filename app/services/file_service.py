import os
import aiofiles
import zipfile
import shutil

class FileService:
    async def read_properties(self, server_dir: str) -> dict:
        props_path = os.path.join(server_dir, "server.properties")
        current_props = {}
        if os.path.exists(props_path):
            async with aiofiles.open(props_path, mode='r') as f:
                lines = await f.readlines()
                for line in lines:
                    if "=" in line and not line.startswith("#"):
                        parts = line.strip().split("=", 1)
                        if len(parts) == 2:
                            current_props[parts[0]] = parts[1]
        return current_props

    async def write_properties(self, server_dir: str, properties: dict):
        props_path = os.path.join(server_dir, "server.properties")
        current_props = await self.read_properties(server_dir)
        current_props.update(properties)
        
        async with aiofiles.open(props_path, mode='w') as f:
            await f.write("#Minecraft Server Properties\n")
            await f.write(f"#{os.getcwd()}\n")
            for k, v in current_props.items():
                val = "true" if v is True else "false" if v is False else str(v)
                await f.write(f"{k}={val}\n")


    def extract_package(self, archive_path: str, destination: str):
        ext = archive_path.lower()
        if ext.endswith(".zip"):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(destination)
        elif ext.endswith(".7z"):
            import py7zr
            with py7zr.SevenZipFile(archive_path, mode='r') as z:
                z.extractall(destination)
        
    async def save_upload(self, file, destination: str):
        async with aiofiles.open(destination, 'wb') as out_file:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                await out_file.write(chunk)

file_service = FileService()
