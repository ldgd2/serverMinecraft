from typing import Dict
import os
from .process import MinecraftServer
from sqlalchemy.orm import Session
from models import Server
import asyncio

class InstanceManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InstanceManager, cls).__new__(cls)
            cls._instance.servers = {} # type: Dict[str, MinecraftServer]
            cls._instance.base_dir = os.path.abspath("servers")
        return cls._instance

    def load_servers_from_db(self, db: Session):
        """Re-hydrate server objects from database on startup"""
        server_records = db.query(Server).all()
        for record in server_records:
            jar_path = os.path.join(self.base_dir, record.name, "server.jar")
            working_dir = os.path.join(self.base_dir, record.name)
            
            instance = MinecraftServer(
                name=record.name,
                ram_mb=record.ram_mb,
                jar_path=jar_path,
                working_dir=working_dir
            )
            self.servers[record.name] = instance

    def get_server(self, name: str) -> MinecraftServer:
        return self.servers.get(name)

    def create_server(self, db: Session, name: str, version: str, ram_mb: int, port: int, online_mode: bool = False):
        if name in self.servers:
            raise ValueError("Server already exists")

        # Create Directory
        server_dir = os.path.join(self.base_dir, name)
        os.makedirs(server_dir, exist_ok=True)
        
        # Create DB Record
        new_server = Server(
            name=name,
            version=version,
            ram_mb=ram_mb,
            port=port,
            online_mode=online_mode,
            motd=f"A Minecraft Server - {name}"
        )
        db.add(new_server)
        db.commit()
        db.refresh(new_server)

        # Initialize Instance
        # Note: jar file is not downloaded yet. That's handled by 'downloader'.
        # We point to where it WILL be.
        instance = MinecraftServer(
            name=name,
            ram_mb=ram_mb,
            jar_path=os.path.join(server_dir, "server.jar"),
            working_dir=server_dir
        )
        self.servers[name] = instance
        return new_server

    def delete_server(self, db: Session, name: str):
        instance = self.servers.get(name)
        if instance:
            if instance.is_running():
                instance.kill()
            del self.servers[name]
        
        # Remove from DB
        record = db.query(Server).filter(Server.name == name).first()
        if record:
            db.delete(record)
            db.commit()
            
        # Remove Files
        server_dir = os.path.join(self.base_dir, name)
        if os.path.exists(server_dir):
            import shutil
            shutil.rmtree(server_dir)

manager = InstanceManager()
