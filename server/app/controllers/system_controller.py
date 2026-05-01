import platform
import psutil
from app.services.system_service import system_manager

DEFAULT_SYSTEM_CONFIG = {
    "SECRET_KEY": "change_me_in_production",
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "1440",
    "DEBUG": "True",
    "SERVICE_NAME": "minecraft-dashboard",
    "DB_ENGINE": "postgresql",
    "DB_HOST": "127.0.0.1",
    "DB_PORT": "5432",
    "DB_NAME": "mine_db",
    "DB_USER": "postgres",
    "DB_PASSWORD": "postgres",
    "DB_POOL_SIZE": "50",
    "DB_MAX_OVERFLOW": "100",
    "DB_ECHO": "False",
    "HOST": "0.0.0.0",
    "PORT": "8000",
    "MASTERBRIDGE_DEFAULT_IP": "127.0.0.1",
    "MASTERBRIDGE_DEFAULT_PORT": "8081"
}

class SystemController:

    def get_service_status(self):
        return {"enabled": system_manager.is_service_enabled(), "os": system_manager.os_type}
    
    def enable_service(self):
        return {"success": system_manager.enable_service()}
    
    def disable_service(self):
        return {"success": system_manager.disable_service()}
    
    def restart_service(self):
        return {"success": system_manager.restart_service()}
    
    def get_system_info(self):
        """Get system resources information"""
        # CPU info
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=0.5)
        
        # RAM info
        memory = psutil.virtual_memory()
        ram_total_mb = memory.total // (1024 * 1024)
        ram_used_mb = memory.used // (1024 * 1024)
        ram_available_mb = memory.available // (1024 * 1024)
        
        # Disk info - use correct path for Windows/Linux
        disk_path = 'C:\\' if platform.system() == 'Windows' else '/'
        disk = psutil.disk_usage(disk_path)
        disk_total_mb = disk.total // (1024 * 1024)
        disk_used_mb = disk.used // (1024 * 1024)
        disk_available_mb = disk.free // (1024 * 1024)
        
        # OS info
        os_name = platform.system()
        
        return {
            "os": os_name,
            "cpu_count": cpu_count,
            "cpu_percent": cpu_percent,
            "ram_total_mb": ram_total_mb,
            "ram_used_mb": ram_used_mb,
            "ram_available_mb": ram_available_mb,
            "disk_total_mb": disk_total_mb,
            "disk_used_mb": disk_used_mb,
            "disk_available_mb": disk_available_mb
        }

    def get_system_stats(self):
        """Get system stats for real-time monitoring"""
        import time
        import os
        
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used // (1024 * 1024)
            memory_total_mb = memory.total // (1024 * 1024)
            
            # Disk - use correct path for Windows/Linux
            disk_path = 'C:\\' if platform.system() == 'Windows' else '/'
            disk = psutil.disk_usage(disk_path)
            disk_percent = disk.percent
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime_seconds = int(time.time() - boot_time)
            
            return {
                "cpu": round(cpu_percent, 1),
                "memory_used": memory_used_mb,
                "memory_total": memory_total_mb,
                "disk": round(disk_percent, 1),
                "uptime": uptime_seconds
            }
        except Exception as e:
            print(f"Error getting system stats: {e}")
            return {
                "cpu": 0,
                "memory_used": 0,
                "memory_total": 1,
                "disk": 0,
                "uptime": 0
            }

    def get_system_config(self) -> dict:
        """Read .env configuration as dictionary merged with defaults"""
        import os
        config = DEFAULT_SYSTEM_CONFIG.copy()
        
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        parts = line.strip().split("=", 1)
                        if len(parts) == 2:
                            config[parts[0]] = parts[1]
        
        # Mask sensitive info
        if "SECRET_KEY" in config:
            config["SECRET_KEY"] = "********"
        return config


    def update_system_config(self, updates: dict):
        """Update .env configuration preserving comments"""
        import os
        lines = []
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                lines = f.readlines()
        
        # Safety: Ignore updating SECRET_KEY if it's the mask value
        if "SECRET_KEY" in updates and updates["SECRET_KEY"] == "********":
            del updates["SECRET_KEY"]

        updated_keys = set()
        new_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Preserve comments and empties
            if stripped.startswith("#") or not stripped:
                 new_lines.append(line)
                 continue
            
            if "=" in line:
                 parts = stripped.split("=", 1)
                 if len(parts) == 2:
                     key = parts[0]
                     if key in updates:
                         new_lines.append(f"{key}={updates[key]}\n")
                         updated_keys.add(key)
                         continue
            new_lines.append(line)

        # Append new keys
        for k, v in updates.items():
            if k not in updated_keys:
                 new_lines.append(f"{k}={v}\n")

        with open(".env", "w") as f:
             f.writelines(new_lines)
        return True


