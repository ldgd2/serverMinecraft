"""
core/paths.py
Centralised path resolution.
  - Resources   → bundled files (works with PyInstaller _MEIPASS)
  - Config/data → %APPDATA%\\MinecraftLauncher  (never inside the .exe folder)
"""
import sys
import os

# ── App name (folder inside AppData) ─────────────────────────────────────────
APP_NAME = "MinecraftLauncher"


def get_appdata_dir() -> str:
    """
    Return the persistent data directory for the launcher.
    Windows : %APPDATA%\\MinecraftLauncher
    macOS   : ~/Library/Application Support/MinecraftLauncher
    Linux   : ~/.config/MinecraftLauncher
    """
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")

    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def get_config_path() -> str:
    """Full path to settings.dat inside the AppData directory."""
    return os.path.join(get_appdata_dir(), "settings.dat")

def get_legacy_config_path() -> str:
    """Full path to the old settings.json for migration."""
    return os.path.join(get_appdata_dir(), "settings.json")


def get_keyfile_path() -> str:
    """Full path to the per-machine encryption key file (AppData)."""
    return os.path.join(get_appdata_dir(), ".keystore")


def get_resource_path(relative_path: str) -> str:
    """
    Resolve a resource path that works both in normal Python and inside a
    PyInstaller bundle (_MEIPASS).
    """
    try:
        base = sys._MEIPASS          # type: ignore[attr-defined]
    except AttributeError:
        base = os.path.abspath(".")
    return os.path.join(base, relative_path)
