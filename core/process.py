import asyncio
import os
import psutil
import shutil
from typing import Optional, List
from asyncio import subprocess

class MinecraftServer:
    def __init__(self, name: str, ram_mb: int, jar_path: str, working_dir: str):
        self.name = name
        self.ram_mb = ram_mb
        self.jar_path = jar_path
        self.working_dir = working_dir
        self.process: Optional[subprocess.Process] = None
        self.log_subscribers: List[asyncio.Queue] = []
    
    async def start(self):
        if self.is_running():
            return
        
        # Build command: java -Xmx...M -jar ... nogui
        cmd = [
            "java",
            f"-Xmx{self.ram_mb}M",
            f"-Xms{max(512, self.ram_mb // 2)}M",
            "-jar",
            self.jar_path,
            "nogui"
        ]
        
        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.working_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        
        # Start background task to read logs
        asyncio.create_task(self._read_log_stream())

    async def stop(self):
        if not self.is_running():
            return
        
        try:
            await self.write("stop")
            # Wait a bit for graceful shutdown
            try:
                await asyncio.wait_for(self.process.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                self.kill()
        except Exception:
            self.kill()

    def kill(self):
        if self.process:
            try:
                self.process.kill()
            except ProcessLookupError:
                pass

    async def write(self, command: str):
        if self.is_running() and self.process.stdin:
            self.process.stdin.write(f"{command}\n".encode())
            await self.process.stdin.drain()

    def is_running(self):
        return self.process is not None and self.process.returncode is None

    async def _read_log_stream(self):
        if not self.process or not self.process.stdout:
            return

        while True:
            line = await self.process.stdout.readline()
            if not line:
                break
            decoded_line = line.decode('utf-8', errors='replace')
            
            # Broadcast to subscribers
            for queue in self.log_subscribers:
                await queue.put(decoded_line)
        
        # Cleanup when process exits
        self.process = None

    def subscribe_logs(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self.log_subscribers.append(q)
        return q

    def unsubscribe_logs(self, q: asyncio.Queue):
        if q in self.log_subscribers:
            self.log_subscribers.remove(q)

    def get_stats(self):
        if not self.is_running() or not self.process:
            return {"status": "OFFLINE", "cpu": 0, "ram": 0}
        
        try:
            sys_proc = psutil.Process(self.process.pid)
            with sys_proc.oneshot():
                cpu = sys_proc.cpu_percent()
                mem = int(sys_proc.memory_info().rss / (1024 * 1024)) # MB as integer
            return {"status": "ONLINE", "cpu": cpu, "ram": mem}
        except psutil.NoSuchProcess:
            return {"status": "OFFLINE", "cpu": 0, "ram": 0}

