import os
import sys
import platform
import subprocess

# But need path to python and run.py

class SystemServiceManager:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.service_name = os.getenv("SERVICE_NAME", "minecraft-dashboard")
        self.python_exec = sys.executable
        self.app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.run_script = os.path.join(self.app_dir, "run.py")

    def is_service_enabled(self):
        # Implementation depends on OS
        if self.os_type == "linux":
            return self._is_service_enabled_linux()
        elif self.os_type == "windows":
            return self._is_service_enabled_windows()
        return False

    def enable_service(self):
        if self.os_type == "linux":
            return self._enable_service_linux()
        elif self.os_type == "windows":
            return self._enable_service_windows()
        return False

    def disable_service(self):
        if self.os_type == "linux":
            return self._disable_service_linux()
        elif self.os_type == "windows":
            return self._disable_service_windows()
        return False

    # --- Linux Implementation (Systemd) ---
    def _get_systemd_path(self):
        return f"/etc/systemd/system/{self.service_name}.service"

    def _is_service_enabled_linux(self):
        return os.path.exists(self._get_systemd_path())

    def _enable_service_linux(self):
        service_content = f"""[Unit]
Description=Minecraft Server Dashboard
After=network.target

[Service]
User={os.getlogin()}
WorkingDirectory={self.app_dir}
ExecStart={self.python_exec} {self.run_script}
Restart=always

[Install]
WantedBy=multi-user.target
"""
        # This requires sudo. The app might not have permission.
        # We can write to a temporary file and try to sudo mv it?
        # Or return the command for the user to run?
        # The user said "the setup... creates a service". Using the dashboard to toggle implies the dashboard has permissions or sudo.
        # We will attempt to write.
        try:
            tmp_path = f"/tmp/{self.service_name}.service"
            with open(tmp_path, "w") as f:
                f.write(service_content)
            
            subprocess.run(["sudo", "mv", tmp_path, self._get_systemd_path()], check=True)
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            subprocess.run(["sudo", "systemctl", "enable", self.service_name], check=True)
            subprocess.run(["sudo", "systemctl", "start", self.service_name], check=True)
            return True
        except Exception as e:
            print(f"Error enabling linux service: {e}")
            return False

    def _disable_service_linux(self):
        try:
            subprocess.run(["sudo", "systemctl", "stop", self.service_name], check=True)
            subprocess.run(["sudo", "systemctl", "disable", self.service_name], check=True)
            subprocess.run(["sudo", "rm", self._get_systemd_path()], check=True)
            subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
            return True
        except Exception as e:
            print(f"Error disabling linux service: {e}")
            return False

    # --- Windows Implementation (SC / Task Scheduler) ---
    def _is_service_enabled_windows(self):
        # Check via sc query and look for RUNNING state
        try:
            res = subprocess.run(["sc", "query", self.service_name], capture_output=True, text=True)
            if res.returncode != 0:
                return False
            return "STATE              : 4  RUNNING" in res.stdout
        except:
            return False

    def _is_service_enabled_linux(self):
        # Check via systemctl is-active
        try:
            res = subprocess.run(["systemctl", "is-active", self.service_name], capture_output=True, text=True)
            return res.stdout.strip() == "active"
        except:
            return False

    def _enable_service_windows(self):
        # Using 'sc create' requires Admin.
        # We assume the user runs the dashboard or setup with Admin if they want this.
        # Command: sc create minecraft-dashboard binPath= "path\to\python.exe path\to\run.py" start= auto
        bin_path = f'"{self.python_exec}" "{self.run_script}"'
        try:
            subprocess.run([
                "sc", "create", self.service_name,
                "binPath=", bin_path,
                "start=", "auto",
                "DisplayName=", "Minecraft Server Dashboard"
            ], check=True)
            subprocess.run(["sc", "start", self.service_name], check=True)
            return True
        except Exception as e:
            print(f"Error enabling windows service: {e}")
            return False

    def _disable_service_windows(self):
        try:
            subprocess.run(["sc", "stop", self.service_name], check=True)
            subprocess.run(["sc", "delete", self.service_name], check=True)
            return True
        except Exception as e:
            print(f"Error disabling windows service: {e}")
            return False

system_manager = SystemServiceManager()
