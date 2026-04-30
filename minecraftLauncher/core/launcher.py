import subprocess
import os
import threading
import minecraft_launcher_lib
from config.manager import config
from core.versions import get_installed_versions

def resolve_version_id_for_loader(base_version, loader_type):
    """Find an installed version id that matches the selected loader and Minecraft base version."""
    if not base_version:
        return base_version

    loader_type = (loader_type or "Vanilla").lower()
    if loader_type == "vanilla":
        return base_version

    installed = get_installed_versions()
    candidates = []

    for installed_version in installed:
        version_lower = installed_version.lower()
        if loader_type == "fabric" and "fabric" in version_lower and base_version in version_lower:
            candidates.append(installed_version)
        elif loader_type == "forge" and "forge" in version_lower and base_version in version_lower:
            candidates.append(installed_version)
        elif loader_type == "optifine" and "optifine" in version_lower and base_version in version_lower:
            candidates.append(installed_version)
        elif base_version in version_lower and loader_type in version_lower:
            candidates.append(installed_version)

    return candidates[0] if candidates else base_version


def download_authlib_injector(minecraft_directory):
    """Descarga authlib-injector.jar si no existe en libraries."""
    import requests
    lib_dir = os.path.join(minecraft_directory, "libraries")
    os.makedirs(lib_dir, exist_ok=True)
    jar_path = os.path.join(lib_dir, "authlib-injector.jar")
    
    if not os.path.exists(jar_path):
        urls = [
            "https://authlib-injector.yggdrasil.live/artifact/latest/authlib-injector.jar",
            "https://bmclapi2.bangbang93.com/mirrors/authlib-injector/artifact/latest/authlib-injector.jar",
            "https://github.com/yushijinhun/authlib-injector/releases/download/v1.2.7/authlib-injector-1.2.7.jar"
        ]
        
        success = False
        last_error = ""
        for url in urls:
            try:
                print(f"[Launcher] Descargando authlib-injector.jar de {url}...")
                response = requests.get(url, stream=True, timeout=10)
                response.raise_for_status()
                with open(jar_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print("[Launcher] Descarga de authlib-injector completa.")
                success = True
                break
            except Exception as e:
                print(f"[-] Falló descarga desde {url}: {e}")
                last_error = str(e)
                if os.path.exists(jar_path):
                     try: os.remove(jar_path) 
                     except: pass

        if not success:
             print(f"[-] Error crítico descargando authlib-injector: {last_error}")
             return None
    return jar_path

def get_profile_path(modloader, version):
    """Generate a unique profile path for the given modloader and version."""
    import minecraft_launcher_lib
    base_dir = config.get("minecraft_dir") or minecraft_launcher_lib.utils.get_minecraft_directory()
    profiles_dir = os.path.join(base_dir, "profiles")
    profile_dir = f"{modloader.lower()}-{version}"
    return os.path.join(profiles_dir, profile_dir)

def setup_profile(modloader, version):
    """Ensure the profile directory exists and is properly initialized."""
    profile_path = get_profile_path(modloader, version)
    os.makedirs(profile_path, exist_ok=True)

    # Create subdirectories for mods, libraries, and configs
    for subdir in ["mods", "libraries", "configs"]:
        os.makedirs(os.path.join(profile_path, subdir), exist_ok=True)

    return profile_path

def launch_minecraft_with_profile(modloader, version):
    """Launch Minecraft using the specified profile."""
    profile_path = setup_profile(modloader, version)
    print(f"Launching Minecraft with profile: {profile_path}")
    # We dynamically inject this into gameDirectory in launch_minecraft below

def launch_minecraft(version_id, callback_dict=None):
    """
    Generates the launch options and starts the Minecraft process.
    Runs asynchronously to avoid blocking the UI.
    To support both Vanilla and Fabric, pass the appropriate version_id.
    """
    def run_process():
        minecraft_directory = config.get("minecraft_dir")
        username = config.get("username")
        ram_mb = config.get("ram_mb")
        java_path = config.get("java_path")
        
        # ── JVM Logic ──
        jvm_mode = config.get("jvm_mode", "auto")
        if jvm_mode == "manual":
            jvm_arguments_str = config.get("jvm_arguments", "")
            jvm_args_list = jvm_arguments_str.split() if jvm_arguments_str else []
        else:
            jvm_args_list = []
            if config.get("jvm_experimental"):
                jvm_args_list.append("-XX:+UnlockExperimentalVMOptions")
            
            gc_type = config.get("jvm_gc", "G1GC")
            if gc_type == "G1GC":
                c_new = config.get("jvm_g1_new_size", 20)
                c_res = config.get("jvm_g1_reserve", 20)
                c_heap = config.get("jvm_g1_heap_region", 32)
                jvm_args_list.extend([
                    "-XX:+UseG1GC", 
                    f"-XX:G1NewSizePercent={c_new}", 
                    f"-XX:G1ReservePercent={c_res}", 
                    "-XX:MaxTenuringThreshold=1", 
                    f"-XX:G1HeapRegionSize={c_heap}M"
                ])
            elif gc_type == "ZGC":
                jvm_args_list.append("-XX:+UseZGC")
            elif gc_type == "Shenandoah":
                jvm_args_list.append("-XX:+UseShenandoahGC")
            elif gc_type == "CMS":
                jvm_args_list.append("-XX:+UseConcMarkSweepGC")
                
            if config.get("jvm_optimize_latency"):
                if gc_type == "G1GC":
                    c_paus = config.get("jvm_max_pause", 50)
                    jvm_args_list.append(f"-XX:MaxGCPauseMillis={c_paus}")
                jvm_args_list.append("-XX:+AlwaysPreTouch")

        # Local Skin Server for Offline Skins
        local_skin_server = None
        auth_url = ""
        enable_local_server = config.get("enable_local_skin_server") or (
            config.get("auth_type") != "premium" and bool(config.get("skin_path"))
        )

        if enable_local_server and config.get("auth_type") != "premium":
            try:
                from core.skin_server import start_local_skin_server
                if callback_dict and 'log' in callback_dict:
                    callback_dict['log']("Starting local skin server...")
                local_skin_server = start_local_skin_server()
                auth_url = f"http://127.0.0.1:{local_skin_server.port}"
            except Exception as e:
                if callback_dict and 'log' in callback_dict:
                    callback_dict['log'](f"Failed to start local skin server: {e}")

        # Authlib Injector
        has_custom_auth = False
        if local_skin_server:
            has_custom_auth = True
        elif config.get("enable_custom_auth") and config.get("auth_api_url"):
            has_custom_auth = True
            auth_url = config.get("auth_api_url")

        if has_custom_auth and auth_url:
            jar_path = download_authlib_injector(minecraft_directory)
            if jar_path and os.path.exists(jar_path):
                jvm_args_list.append(f"-javaagent:{jar_path}={auth_url}")
                if callback_dict and 'log' in callback_dict:
                    callback_dict['log'](f"Authlib Injector applied with: {auth_url}")

        from core.security import decrypt_data
        selected_loader = config.get("selected_type", "Vanilla")
        version_to_launch = resolve_version_id_for_loader(version_id, selected_loader)
        if version_to_launch != version_id and callback_dict and 'log' in callback_dict:
            callback_dict['log'](f"Detected {selected_loader} profile: {version_to_launch}")

        # Generate offline UUID if none exists
        uid = config.get("uuid")
        if not uid:
            import uuid
            uid = str(uuid.uuid3(uuid.NAMESPACE_DNS, f"OfflinePlayer:{username}")).replace("-", "")

        # Generate RAM arguments safely
        ram_args = []
        if not (jvm_mode == "manual" and ("-Xmx" in jvm_arguments_str or "-Xms" in jvm_arguments_str)):
            ram_args = [f"-Xmx{ram_mb}M", f"-Xms{ram_mb}M"]

        # Setting up launch options
        options = {
            "username": username,
            "uuid": uid, 
            "token": decrypt_data(config.get("auth_token") or ""), 
            "user_type": "msa" if config.get("auth_type") == "premium" else "legacy",
            "jvmArguments": jvm_args_list + ram_args,
            "gameDirectory": os.path.join(minecraft_directory, "profiles", version_to_launch),
            "launcherName": "CustomPythonLauncher",
            "launcherVersion": "1.0",
        }

        # Ensure per-version profile directory and isolated mods folder exist
        profile_dir = options["gameDirectory"]
        os.makedirs(os.path.join(profile_dir, "mods"), exist_ok=True)
        if callback_dict and 'log' in callback_dict:
            callback_dict['log'](f"Perfil: {profile_dir}")


        if java_path and os.path.exists(java_path):
            options["executablePath"] = java_path

        # Emit log message via callback if available
        if callback_dict and 'log' in callback_dict:
            callback_dict['log'](f"Generating launch command for {version_id}...")

        try:
            command = minecraft_launcher_lib.command.get_minecraft_command(version_to_launch, minecraft_directory, options)
            
            # Inject auto-join parameters
            acc_type = config.get("account_type", "guest")
            if acc_type in ["premium", "server"]:
                auto_ip = config.get("auto_join_ip")
                if auto_ip:
                    if ":" in auto_ip:
                        ip, port = auto_ip.split(":", 1)
                        command.extend(["--server", ip, "--port", port])
                    else:
                        command.extend(["--server", auto_ip])
            
            # Inject Fullscreen
            if config.get("fullscreen"):
                command.append("--fullscreen")
            
            # Log the exact command for debugging
            log_path = os.path.join(os.path.abspath("."), "launch_command.log")
            with open(log_path, "w", encoding="utf-8") as lf:
                lf.write(f"--- Launch Command Debug ---\n")
                lf.write(f"Options passed: {options}\n\n")
                lf.write(f"Command array:\n")
                for arg in command:
                    lf.write(f"{arg}\n")
            
            if callback_dict and 'log' in callback_dict:
                callback_dict['log']("Starting process...")
                
            # Execute process
            
            # Use specific startup info to hide console window on windows if possible
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                startupinfo=startupinfo,
                text=True # Decode stdout/stderr
            )

            # Skin Sync Monitor
            if config.get("enable_skin_sync") and config.get("server_ip") and config.get("api_url"):
                from core.skin_sync import start_skin_sync_monitor
                log_file = os.path.join(options["gameDirectory"], "logs", "latest.log")
                start_skin_sync_monitor(
                    f_log=log_file,
                    ip=config.get("server_ip"),
                    username=options["username"],
                    uuid=options["uuid"],
                    api_url=config.get("api_url")
                )

            # Signal that process started
            if callback_dict and 'started' in callback_dict:
                callback_dict['started']()

            # Read stdout line by line
            while True:
                output = process.stdout.readline()
                if output == "" and process.poll() is not None:
                    break
                if output:
                    if callback_dict and 'log' in callback_dict:
                        callback_dict['log'](output.strip())
                        
            # Wait for process to finish
            rc = process.poll()
            
            # Stop local skin server if running
            if local_skin_server:
                if callback_dict and 'log' in callback_dict:
                    callback_dict['log']("Stopping local skin server... ")
                local_skin_server.stop()

            if callback_dict and 'finished' in callback_dict:
                callback_dict['finished'](rc)

        except Exception as e:
            if callback_dict and 'log' in callback_dict:
                callback_dict['log'](f"Error launching Minecraft: {e}")
            if callback_dict and 'finished' in callback_dict:
                 callback_dict['finished'](-1)
                 
    # Run in a separate thread so we don't block the main application thread (UI)
    thread = threading.Thread(target=run_process)
    thread.daemon = True
    thread.start()

def get_versions_by_profile(modloader):
    """Retrieve all versions available for a specific modloader profile."""
    from core.versions import get_installed_versions
    installed = get_installed_versions()
    modloader = (modloader or "Vanilla").lower()
    
    filtered = []
    for v in installed:
        v_lower = v.lower()
        if modloader == "vanilla":
             if "fabric" not in v_lower and "forge" not in v_lower and "optifine" not in v_lower:
                 filtered.append(v)
        else:
             if modloader in v_lower:
                 filtered.append(v)
    return filtered

def filter_versions(modloader, base_version):
    """Filter versions by modloader and Minecraft base version."""
    modloader_versions = get_versions_by_profile(modloader)
    if not base_version:
        return modloader_versions
    return [v for v in modloader_versions if base_version in v]
