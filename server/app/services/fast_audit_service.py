import mmap
import os
import struct
import time
import threading
from datetime import datetime

class FastAuditLogger:
    """
    Zero-Copy High-Performance Audit Logger.
    Uses memory-mapped files (mmap) for instant persistence of log events.
    Bypasses standard SQL overhead for high-frequency events.
    """
    def __init__(self, filepath: str = "data/audit_fast.bin", capacity: int = 10000):
        self.capacity = capacity
        # Record format: timestamp (d), severity_code (B), username (32s), action (64s) = 8 + 1 + 32 + 64 = 105 bytes
        self.record_format = "dB32s64s"
        self.record_size = struct.calcsize(self.record_format)
        self.file_size = self.record_size * capacity
        self.filepath = filepath
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        if not os.path.exists(filepath):
            with open(filepath, "wb") as f:
                f.write(b'\x00' * self.file_size)
        
        self.f = open(filepath, "r+b")
        self.mm = mmap.mmap(self.f.fileno(), self.file_size)
        self.lock = threading.Lock()
        
        # Pointer to the next record (stored in the first 4 bytes of a separate file or at the end)
        self.index_path = filepath + ".idx"
        self._current_index = 0
        if os.path.exists(self.index_path):
            with open(self.index_path, "rb") as f:
                data = f.read(4)
                if data: self._current_index = struct.unpack("I", data)[0]

    def log(self, username: str, action: str, severity: int = 1):
        """
        Log an entry with Zero-Copy speed.
        Severity: 0=DEBUG, 1=INFO, 2=WARN, 3=ERROR
        """
        with self.lock:
            offset = self._current_index * self.record_size
            
            # Prepare data (truncate if too long)
            u_bytes = username.encode('utf-8')[:32].ljust(32, b'\x00')
            a_bytes = action.encode('utf-8')[:64].ljust(64, b'\x00')
            
            # Pack and write directly to memory-mapped file
            data = struct.pack(self.record_format, time.time(), severity, u_bytes, a_bytes)
            self.mm[offset : offset + self.record_size] = data
            
            # Increment and wrap index (Circular Buffer)
            self._current_index = (self._current_index + 1) % self.capacity
            
            # Persist index (non-critical, can be done periodically for even more speed)
            with open(self.index_path, "wb") as f:
                f.write(struct.pack("I", self._current_index))

    def get_recent(self, count: int = 50):
        """Read recent logs directly from memory mapping."""
        logs = []
        with self.lock:
            idx = self._current_index
            for i in range(min(count, self.capacity)):
                idx = (idx - 1) % self.capacity
                offset = idx * self.record_size
                data = self.mm[offset : offset + self.record_size]
                
                # Check if record is empty
                if data[0:8] == b'\x00' * 8: continue
                
                ts, sev, u, a = struct.unpack(self.record_format, data)
                logs.append({
                    "timestamp": datetime.fromtimestamp(ts).isoformat(),
                    "severity": sev,
                    "username": u.decode('utf-8').strip('\x00'),
                    "action": a.decode('utf-8').strip('\x00')
                })
        return logs

    def close(self):
        self.mm.close()
        self.f.close()

# Singleton instance
fast_audit = FastAuditLogger()
