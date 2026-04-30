"""
core/security.py
Strong symmetric encryption for auth tokens.

Key derivation:
  1. Generate a 32-byte random salt once, stored in %APPDATA%\\MinecraftLauncher\\.keystore
  2. Derive a Fernet key via PBKDF2-HMAC-SHA256 from:
       - salt (random, persistent)
       - machine fingerprint (MAC address, CPU info)
  This means the key is:
       - Unique per machine (another PC cannot decrypt tokens)
       - Stable across launcher restarts (salt persists)
       - Not trivially reversible (PBKDF2 with 480 000 iterations)
"""
import os
import hashlib
import hmac
import base64
import platform
import uuid as _uuid_mod
from cryptography.fernet import Fernet, InvalidToken


# ── Key derivation ─────────────────────────────────────────────────────────────

_KEY_CACHE: bytes | None = None


def _machine_fingerprint() -> bytes:
    """Build a stable, unique bytes fingerprint from hardware identifiers."""
    parts = [
        str(_uuid_mod.getnode()),           # MAC address
        platform.node(),                    # hostname
        platform.processor() or "cpu",      # CPU string
    ]
    return "|".join(parts).encode("utf-8")


def _load_or_create_salt() -> bytes:
    """
    Load the persistent random salt from %APPDATA%/.keystore.
    Creates it (32 random bytes) if it does not exist yet.
    """
    from core.paths import get_keyfile_path
    path = get_keyfile_path()
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                salt = f.read()
            if len(salt) >= 32:
                return salt[:32]
        except OSError:
            pass
    # First run: generate and persist
    salt = os.urandom(32)
    try:
        with open(path, "wb") as f:
            f.write(salt)
        # Hide the file on Windows
        if os.name == "nt":
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(path, 0x2)  # FILE_ATTRIBUTE_HIDDEN
    except OSError:
        pass
    return salt


def _get_fernet() -> Fernet:
    """Return a cached Fernet instance bound to this machine."""
    global _KEY_CACHE
    if _KEY_CACHE is None:
        salt        = _load_or_create_salt()
        fingerprint = _machine_fingerprint()
        raw_key     = hashlib.pbkdf2_hmac(
            hash_name   = "sha256",
            password    = fingerprint,
            salt        = salt,
            iterations  = 480_000,
            dklen       = 32,
        )
        _KEY_CACHE = base64.urlsafe_b64encode(raw_key)
    return Fernet(_KEY_CACHE)


# ── Public API ─────────────────────────────────────────────────────────────────

def encrypt_data(text: str) -> str:
    """
    Encrypt a plaintext string.
    Returns a URL-safe base64 Fernet token (string).
    Returns "" if text is empty.
    """
    if not text:
        return ""
    try:
        return _get_fernet().encrypt(text.encode("utf-8")).decode("utf-8")
    except Exception as e:
        print(f"[Security] encrypt_data error: {e}")
        return ""


def decrypt_data(cipher: str) -> str:
    """
    Decrypt a Fernet token back to its plaintext.
    Returns "" on any error (bad key, tampered data, etc.).
    """
    if not cipher:
        return ""
    try:
        return _get_fernet().decrypt(cipher.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        print("[Security] decrypt_data: token invalid or key mismatch.")
        return ""
    except Exception as e:
        print(f"[Security] decrypt_data error: {e}")
        return ""


def rotate_encryption(old_plain: str) -> str:
    """
    Re-encrypt a value (useful after a machine fingerprint change).
    Returns the new cipher or "" if re-encryption failed.
    """
    if not old_plain:
        return ""
    return encrypt_data(old_plain)
