"""
config/manager.py
Persistent settings manager.
Settings are stored in %APPDATA%\\MinecraftLauncher\\settings.json
"""
import json
import os
from core.paths import get_config_path, get_legacy_config_path, get_appdata_dir
from core.security import encrypt_data, decrypt_data

CONFIG_FILE = get_config_path()
LEGACY_CONFIG_FILE = get_legacy_config_path()

# Sensible defaults — never store sensitive values (tokens) here plain-text
DEFAULT_CONFIG = {
    # ── Identity ────────────────────────────────────────────────────────────
    "username":     "Player",
    "uuid":         "",
    "auth_type":    "nopremium",    # "premium" | "nopremium"
    "logged_in":    False,
    "auth_token":   "",             # Always Fernet-encrypted
    "player_token": "",             # LiderAuth JWT token
    "password":     "",             # For auto-login
    "ms_refresh_token": "",         # For premium auto-login
    "guest_username": "",

    # ── Launcher ─────────────────────────────────────────────────────────────
    "selected_version": "",
    "selected_type":    "Vanilla",  # "Vanilla" | "Fabric" | "Forge"

    # ── Directories ──────────────────────────────────────────────────────────
    "minecraft_dir": os.path.join(get_appdata_dir(), "game"),

    # ── Java / Performance ───────────────────────────────────────────────────
    "ram_mb":        4096,
    "java_path":     "",
    "jvm_arguments": (
        "-XX:+UnlockExperimentalVMOptions "
        "-XX:+UseG1GC "
        "-XX:G1NewSizePercent=20 "
        "-XX:G1ReservePercent=20 "
        "-XX:MaxGCPauseMillis=50 "
        "-XX:G1HeapRegionSize=32M"
    ),

    # ── No-Premium server ─────────────────────────────────────────────────────
    "server_ip":        "",
    "server_port":      25565,
    "server_name":      "Lider Server",
    "api_url":          "",
    "api_key":          "",             # For bridge endpoints
    "auth_api_url":     "",
    "server_id":        1,
    "enable_custom_auth": False,

    # ── Skin ─────────────────────────────────────────────────────────────────
    "skin_path":               "",
    "saved_skins":             [],          # list of paths
    "skin_variant":            "classic",   # "classic" | "slim"
    "enable_skin_sync":        False,
    "enable_local_skin_server": True,

    # ── Premium / Microsoft ───────────────────────────────────────────────────
    "microsoft_client_id":  "ca6c2dc0-164d-4be0-be4a-96f89a01ac12",
    "ms_redirect_uri":      "http://localhost:3000/callback",

    # ── Gameplay ──────────────────────────────────────────────────────────────
    "fullscreen":           False,
    "render_distance":      10,
    "show_fps":             False,
    "close_launcher_on_start": True,

    # ── Misc ─────────────────────────────────────────────────────────────────
    "language":         "es_ES",
    "discord_rpc":      True,
    "check_updates":    True,
    "auto_sync_mods":   True,
    "log_level":        "INFO",     # "DEBUG" | "INFO" | "WARNING"
    "jvm_mode":         "manual",   # "auto" | "manual"
}

# Keys that must never be written to disk in plain-text
_SENSITIVE_KEYS = {"auth_token"}


class ConfigManager:
    """Thread-safe, AppData-backed settings manager."""

    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self._load()

    def _load(self):
        loaded = False
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    encrypted_data = f.read()
                decrypted_json = decrypt_data(encrypted_data)
                if decrypted_json:
                    saved = json.loads(decrypted_json)
                    for k, v in saved.items():
                        if k in self.config:
                            self.config[k] = v
                    loaded = True
                else:
                    print("[Config] Decryption failed or empty. Using defaults.")
            except Exception as e:
                print(f"[Config] Binary load error: {e}. Using defaults.")

        # Legagy Migration if binary doesn't exist
        if not loaded and os.path.exists(LEGACY_CONFIG_FILE):
            try:
                with open(LEGACY_CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                for k, v in saved.items():
                    if k in self.config:
                        self.config[k] = v
                print("[Config] Migrated legacy JSON to encrypted binary format.")
                self.save()  # Create the new binary file
                try:
                    os.remove(LEGACY_CONFIG_FILE) # delete the plain-text
                except: pass
            except Exception as e:
                print(f"[Config] Legacy load error: {e}. Using defaults.")

        # Ensure game directory exists
        os.makedirs(self.config["minecraft_dir"], exist_ok=True)

    def save(self):
        """Write config to disk as an encrypted blob."""
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            json_str = json.dumps(self.config, ensure_ascii=False)
            encrypted_data = encrypt_data(json_str)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write(encrypted_data)
        except Exception as e:
            print(f"[Config] Save error: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        """Set a value and auto-save. Accepts any key (allows runtime-only keys too)."""
        self.config[key] = value
        self.save()

    def reset(self):
        """Reset all values to defaults and save."""
        self.config = DEFAULT_CONFIG.copy()
        self.save()


# Global singleton
config = ConfigManager()
