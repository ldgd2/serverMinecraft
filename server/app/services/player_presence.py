import hashlib
import struct
from typing import List, Set
import threading
import mmap
import os

class BloomFilter:
    """
    A Zero-Copy Bloom Filter implementation using memory-mapped files (mmap).
    Allows the OS to manage the bit array directly, bypassing CPU-heavy copies
    and providing persistent, high-performance bit-level verification.
    """
    def __init__(self, filepath: str = "data/player_presence.bin", size_bits: int = 8000000, hash_count: int = 7):
        self.size = size_bits
        self.hash_count = hash_count
        self.filepath = filepath
        self.file_size = (size_bits // 8) + 1
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Open or create the file
        if not os.path.exists(filepath):
            with open(filepath, "wb") as f:
                f.write(b'\x00' * self.file_size)
        
        self.f = open(filepath, "r+b")
        # ZERO-COPY: Map the file directly into memory
        self.bit_array = mmap.mmap(self.f.fileno(), self.file_size)
        
        self.lock = threading.Lock()
        self._count = 0

    def _hashes(self, item: str) -> List[int]:
        """Generate multiple hash values for an item using fast bit-level hashing."""
        # Use two fast hashes to generate N indices (Double Hashing)
        h1 = int(hashlib.sha256(item.encode()).hexdigest(), 16)
        h2 = int(hashlib.md5(item.encode()).hexdigest(), 16)
        
        hashes = []
        for i in range(self.hash_count):
            hashes.append((h1 + i * h2) % self.size)
        return hashes

    def add(self, item: str):
        """Add an item to the filter (Thread-safe bit setting)."""
        with self.lock:
            for h in self._hashes(item):
                byte_index = h // 8
                bit_index = h % 8
                # Bit manipulation directly in the memory-mapped file
                self.bit_array[byte_index] |= (1 << bit_index)
            self._count += 1

    def __contains__(self, item: str) -> bool:
        """Check if an item might be in the filter (Zero-copy read)."""
        for h in self._hashes(item):
            byte_index = h // 8
            bit_index = h % 8
            if not (self.bit_array[byte_index] & (1 << bit_index)):
                return False
        return True

    def close(self):
        """Close mapping and file handle."""
        self.bit_array.close()
        self.f.close()

class PlayerPresenceService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(PlayerPresenceService, cls).__new__(cls)
                cls._instance.filter = BloomFilter()
                cls._instance._initialized = False
        return cls._instance

    def initialize(self, usernames: List[str]):
        """Bulk load usernames into the Zero-Copy filter."""
        for name in usernames:
            self.filter.add(name.lower())
        self._initialized = True
        print(f"[ZeroCopy-BloomFilter] Initialized and Mapped with {len(usernames)} players.")

    def is_registered(self, username: str) -> bool:
        """Bit-level verification (Zero-Copy)."""
        if not username: return False
        return username.lower() in self.filter

    def register_new(self, username: str):
        """Update the mapped filter."""
        self.filter.add(username.lower())

# Singleton instance
player_presence = PlayerPresenceService()

# Singleton instance
player_presence = PlayerPresenceService()
