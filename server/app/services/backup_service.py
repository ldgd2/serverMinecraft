import os
import subprocess
import shutil
import tarfile
import logging
from datetime import datetime

logger = logging.getLogger("backup_service")

class BackupService:
    def __init__(self, backup_dir="backups", servers_dir="servers", loaders_dir="mod_loaders"):
        self.backup_dir = backup_dir
        self.servers_dir = servers_dir
        self.loaders_dir = loaders_dir
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def create_full_backup(self):
        """Creates a complete backup: Database + Server Files (Mods, Worlds, etc.)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"full_backup_{timestamp}"
        temp_dir = os.path.join(self.backup_dir, f"temp_{timestamp}")
        os.makedirs(temp_dir)

        try:
            # 1. Backup Database into temp dir
            logger.info("Backing up database...")
            db_filename = self._backup_database_to_path(temp_dir)
            
            # 2. Add server files (we'll compress them directly into the final tar)
            final_tar_path = os.path.join(self.backup_dir, f"{backup_name}.tar.gz")
            
            logger.info("Compressing all files (Servers + Database)...")
            with tarfile.open(final_tar_path, "w:gz") as tar:
                # Add the database dump
                tar.add(temp_dir, arcname="database_backup")
                # Add the servers directory
                if os.path.exists(self.servers_dir):
                    tar.add(self.servers_dir, arcname="servers")
                # Add the mod loaders directory
                if os.path.exists(self.loaders_dir):
                    tar.add(self.loaders_dir, arcname="mod_loaders")
                
            return f"{backup_name}.tar.gz"

        finally:
            # Cleanup temp database dump
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def _backup_database_to_path(self, target_path):
        engine_type = os.getenv("DB_ENGINE", "postgresql").lower()
        if engine_type == "sqlite":
            db_path = os.path.join("database", "minecraft.db")
            dest = os.path.join(target_path, "minecraft.db")
            if os.path.exists(db_path):
                shutil.copy2(db_path, dest)
            return "minecraft.db"
        else:
            db_name = os.getenv("DB_NAME")
            dest = os.path.join(target_path, f"{db_name}.sql")
            os.environ["PGPASSWORD"] = os.getenv("DB_PASSWORD", "")
            cmd = [
                "pg_dump", "-h", os.getenv("DB_HOST", "127.0.0.1"),
                "-p", os.getenv("DB_PORT", "5432"),
                "-U", os.getenv("DB_USER", "postgres"),
                "-F", "p", "-f", dest, db_name
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return f"{db_name}.sql"

    def restore_full_backup(self, filename):
        """Restores everything: Overwrites Server Files and Database."""
        backup_path = os.path.join(self.backup_dir, filename)
        if not os.path.exists(backup_path):
            raise Exception("Backup file not found")

        temp_extract = os.path.join(self.backup_dir, "temp_restore")
        if os.path.exists(temp_extract): shutil.rmtree(temp_extract)
        os.makedirs(temp_extract)

        try:
            # 1. Extract everything
            logger.info("Extracting backup archive...")
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(path=temp_extract)

            # 2. Restore Server Files
            logger.info("Restoring server files...")
            extracted_servers = os.path.join(temp_extract, "servers")
            if os.path.exists(extracted_servers):
                if os.path.exists(self.servers_dir):
                    shutil.rmtree(self.servers_dir)
                shutil.copytree(extracted_servers, self.servers_dir)

            # 3. Restore Mod Loaders
            logger.info("Restoring mod loaders...")
            extracted_loaders = os.path.join(temp_extract, "mod_loaders")
            if os.path.exists(extracted_loaders):
                if os.path.exists(self.loaders_dir):
                    shutil.rmtree(self.loaders_dir)
                shutil.copytree(extracted_loaders, self.loaders_dir)

            # 4. Restore Database
            logger.info("Restoring database...")
            db_dir = os.path.join(temp_extract, "database_backup")
            engine_type = os.getenv("DB_ENGINE", "postgresql").lower()
            
            if engine_type == "sqlite":
                extracted_db = os.path.join(db_dir, "minecraft.db")
                if os.path.exists(extracted_db):
                    shutil.copy2(extracted_db, os.path.join("database", "minecraft.db"))
            else:
                db_name = os.getenv("DB_NAME")
                sql_file = os.path.join(db_dir, f"{db_name}.sql")
                if os.path.exists(sql_file):
                    os.environ["PGPASSWORD"] = os.getenv("DB_PASSWORD", "")
                    cmd = [
                        "psql", "-h", os.getenv("DB_HOST", "127.0.0.1"),
                        "-p", os.getenv("DB_PORT", "5432"),
                        "-U", os.getenv("DB_USER", "postgres"),
                        "-d", db_name, "-f", sql_file
                    ]
                    subprocess.run(cmd, check=True, capture_output=True)

            return True

        finally:
            if os.path.exists(temp_extract):
                shutil.rmtree(temp_extract)

    def list_backups(self):
        if not os.path.exists(self.backup_dir): return []
        backups = []
        for f in os.listdir(self.backup_dir):
            if f.endswith(".tar.gz"):
                path = os.path.join(self.backup_dir, f)
                stats = os.stat(path)
                backups.append({
                    "filename": f,
                    "size": stats.st_size,
                    "created_at": datetime.fromtimestamp(stats.st_mtime).isoformat()
                })
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)

    def delete_backup(self, filename):
        path = os.path.join(self.backup_dir, filename)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
