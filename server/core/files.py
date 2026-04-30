import os
import aiofiles
import zipfile
import shutil

async def write_properties(server_dir: str, properties: dict):
    """Reads existing server.properties and updates provided keys, or creates new."""
    props_path = os.path.join(server_dir, "server.properties")
    
    current_props = {}
    if os.path.exists(props_path):
        async with aiofiles.open(props_path, mode='r') as f:
            lines = await f.readlines()
            for line in lines:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    current_props[key] = value

    # Update with new values
    current_props.update(properties)
    
    # Write back
    async with aiofiles.open(props_path, mode='w') as f:
        # Write header
        await f.write("#Minecraft Server Properties\n")
        await f.write(f"#{os.getcwd()}\n")
        
        for k, v in current_props.items():
            # Convert boolean to string lower if needed
            if isinstance(v, bool):
                val = "true" if v else "false"
            else:
                val = str(v)
            await f.write(f"{k}={val}\n")

def extract_package(archive_path: str, destination: str):
    """Extracts zip files to destination."""
    if archive_path.endswith(".zip"):
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(destination)
    # Add rar support if needed later, requires unrar tool usually
    
async def save_upload(file, destination: str):
    async with aiofiles.open(destination, 'wb') as out_file:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            await out_file.write(chunk)
