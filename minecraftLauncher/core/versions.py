import minecraft_launcher_lib
import requests
from config.manager import config

def get_installed_versions():
    """Returns a list of versions currently installed in the minecraft directory"""
    return [v["id"] for v in minecraft_launcher_lib.utils.get_installed_versions(config.get("minecraft_dir"))]

def get_available_vanilla_versions():
    """Fetches the list of all available vanilla releases"""
    try:
        versions = minecraft_launcher_lib.utils.get_version_list()
        # Filter for releases only to keep it clean, though we could show snapshots
        return [v["id"] for v in versions if v["type"] == "release"]
    except Exception as e:
        print(f"Error fetching vanilla versions: {e}")
        return []

def get_available_fabric_versions(mc_version):
    """Fetches available fabric loader versions for a specific Minecraft version"""
    try:
        # Fabric meta API returns loaders for a game version
        url = f"https://meta.fabricmc.net/v2/versions/loader/{mc_version}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return [loader["loader"]["version"] for loader in data]
    except Exception as e:
        print(f"Error fetching fabric versions: {e}")
        return []

def install_vanilla_version(version_id, callback_dict=None):
    """Installs a Vanilla version via minecraft_launcher_lib"""
    minecraft_launcher_lib.install.install_minecraft_version(
        versionid=version_id, 
        minecraft_directory=config.get("minecraft_dir"), 
        callback=callback_dict
    )

def install_fabric_version(mc_version, loader_version, callback_dict=None):
    """Installs a Fabric version via minecraft_launcher_lib"""
    minecraft_launcher_lib.fabric.install_fabric(
        minecraft_version=mc_version,
        minecraft_directory=config.get("minecraft_dir"),
        loader_version=loader_version,
        callback=callback_dict
    )
