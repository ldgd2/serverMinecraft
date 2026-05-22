import os

# 1. Update server/routes/servers.py
routes_path = "server/routes/servers.py"
with open(routes_path, "r", encoding="utf-8") as f:
    content = f.read()

endpoint_code = """
@router.get("/{name}/world/export")
async def export_server_world(name: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        zip_path = await server_controller.export_world(db, name)
        return FileResponse(
            path=zip_path,
            filename=f"{name}_world.zip",
            media_type="application/zip",
            background=None
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Server or world not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
"""

if "export_server_world" not in content:
    with open(routes_path, "a", encoding="utf-8") as f:
        f.write("\n" + endpoint_code + "\n")

# 2. Update server_controller.py
controller_path = "server/app/controllers/server_controller.py"
with open(controller_path, "r", encoding="utf-8") as f:
    content = f.read()

controller_code = """
    async def export_world(self, db: Session, name: str) -> str:
        return await server_service.export_world(db, name)
"""

if "def export_world(" not in content:
    content = content.replace("async def export_server(self", controller_code.lstrip() + "\n    async def export_server(self")
    with open(controller_path, "w", encoding="utf-8") as f:
        f.write(content)

# 3. Update service.py
service_path = "server/app/services/minecraft/service.py"
with open(service_path, "r", encoding="utf-8") as f:
    content = f.read()

service_code = """
    async def export_world(self, db: Session, name: str) -> str:
        import zipfile
        import tempfile
        server = db.query(Server).filter(Server.name == name).first()
        if not server: raise FileNotFoundError(f"Server '{name}' not found")
        server_dir = os.path.join(self.base_dir, name)
        world_dir = os.path.join(server_dir, "world")
        if not os.path.exists(world_dir):
            level_name = "world"
            props_path = os.path.join(server_dir, "server.properties")
            if os.path.exists(props_path):
                with open(props_path, "r") as f:
                    for line in f:
                        if line.startswith("level-name="):
                            level_name = line.strip().split("=", 1)[1]
                            break
            world_dir = os.path.join(server_dir, level_name)
            if not os.path.exists(world_dir): raise FileNotFoundError(f"World directory not found for server: {name}")
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip', prefix=f'{name}_world_')
        try:
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(world_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, world_dir)
                        zipf.write(file_path, arcname)
            return temp_zip.name
        except Exception as e:
            if os.path.exists(temp_zip.name): os.remove(temp_zip.name)
            raise
"""

if "def export_world(" not in content:
    content = content.replace("async def export_server(self", service_code.lstrip() + "\n    async def export_server(self")
    with open(service_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Done updating backend files.")
