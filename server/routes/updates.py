"""
Endpoint de actualizaciones para Launcher y App móvil.

Flujo de publicación:
  1. El empaquetador local compila el exe/apk
  2. Llama POST /api/v1/updates/upload/{platform}/{version} con el binario
  3. El servidor lo guarda en static/versions/{platform}/{version}/
     y actualiza el puntero en versions.json automáticamente.
  4. Los clientes consultan GET /check/{platform} para saber si deben actualizar.

No se necesita git push ni SCP. Solo API.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from routes.auth import get_current_user
from pydantic import BaseModel
from typing import Optional
import os, json, re

router = APIRouter(prefix="/updates", tags=["Updates"])

# ── Rutas ────────────────────────────────────────────────────────────────────

_BASE_DIR  = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "static", "versions"))
_JSON_FILE = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "static", "versions.json"))

_PLATFORM_FILE = {
    "launcher": "launcher.exe",
    "app":      "app.apk",
    "modclient": "minebridge-client.jar",
    "modserver": "minebridge-server.jar",
}

# Auto-crear directorios base al importar el módulo (arranque del servidor)
def _ensure_base_dirs():
    for platform in _PLATFORM_FILE:
        d = os.path.join(_BASE_DIR, platform)
        if not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
            print(f"[updates] Creado directorio: {d}")

_ensure_base_dirs()

# ── Helpers ───────────────────────────────────────────────────────────────────

def _load() -> dict:
    if os.path.exists(_JSON_FILE):
        with open(_JSON_FILE) as f:
            return json.load(f)
    return {"launcher": "1.0.0", "app": "1.0.0", "modclient": "1.0.0", "modserver": "1.0.0"}

def _save(data: dict):
    os.makedirs(os.path.dirname(_JSON_FILE), exist_ok=True)
    with open(_JSON_FILE, "w") as f:
        json.dump(data, f, indent=2)

def _version_tuple(v: str):
    try:
        return tuple(int(x) for x in str(v).strip().split("."))
    except Exception:
        return (0, 0, 0)

def _latest_version(platform: str) -> str:
    data = _load()
    if platform in data:
        return str(data[platform])
    folder = os.path.join(_BASE_DIR, platform)
    if os.path.isdir(folder):
        versions = [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))]
        if versions:
            return sorted(versions, key=_version_tuple)[-1]
    return "1.0.0"

def _download_url(request: Request, platform: str, version: str) -> Optional[str]:
    filename = _PLATFORM_FILE.get(platform)
    if not filename:
        return None
    file_path = os.path.join(_BASE_DIR, platform, version, filename)
    if not os.path.exists(file_path):
        return None
    base = str(request.base_url).rstrip("/")
    return f"{base}/static/versions/{platform}/{version}/{filename}"

def _validate_platform(platform: str):
    if platform not in _PLATFORM_FILE:
        raise HTTPException(status_code=400, detail=f"platform must be one of {list(_PLATFORM_FILE.keys())}")

def _validate_version(version: str):
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        raise HTTPException(status_code=422, detail="version must be X.Y.Z format")

async def _apply_server_mod_update(new_mod_path: str):
    """
    Background task:
    1. Notifica a los jugadores.
    2. Espera 5 min (aqui usamos 5 min para produccion o 1 minuto para test).
    3. Detiene servers, copia el mod, y los reinicia.
    """
    import asyncio
    import shutil
    import traceback
    from database.connection import SessionLocal
    from database.models.server import Server
    from app.controllers.server_controller import ServerController
    
    print("[updates] Iniciando Background Task: Actualizacion automatica del Server Mod")
    sc = ServerController()
    db = SessionLocal()
    try:
        servers = db.query(Server).all()
        # Avisar a todos
        for s in servers:
            try:
                await sc.send_command(s.name, 'minebridge_update 300')
            except Exception: pass
        
        # Esperar 5 minutos
        await asyncio.sleep(300)
        
        # Último aviso 1 minuto antes (si quisieramos)
        
        # Apagar y actualizar
        for s in servers:
            try:
                # Kickear a los jugadores
                await sc.send_command(s.name, 'kick @a §cServidor en actualización automática. Vuelve en un minuto.')
                await asyncio.sleep(2)
                
                # Detener
                await sc.stop_server(s.name)
                # Esperar hasta 20s para que se detenga
                for _ in range(10):
                    await asyncio.sleep(2)
                    
                # Reemplazar archivo en mods/
                mod_dir = os.path.join("servers", s.name, "mods")
                if os.path.exists(mod_dir):
                    for f in os.listdir(mod_dir):
                        if "minebridge" in f.lower() and f.endswith(".jar"):
                            try:
                                os.remove(os.path.join(mod_dir, f))
                            except: pass
                    # Copiar el nuevo
                    shutil.copy2(new_mod_path, os.path.join(mod_dir, _PLATFORM_FILE["modserver"]))
                    print(f"[updates] Mod reemplazado en {s.name}")
                    
                # Reiniciar
                await sc.start_server(s.name)
            except Exception as e:
                print(f"[updates] Error actualizando {s.name}: {e}")
                
    except Exception as e:
        print(f"[updates] Error grave en update task: {e}")
        traceback.print_exc()
    finally:
        db.close()

# ── Endpoints públicos ────────────────────────────────────────────────────────

@router.get("/check/{platform}", summary="Verificar nueva versión")
def check_update(platform: str, current_version: str, request: Request):
    """
    El cliente envía su versión actual (?current_version=1.0.0).
    Responde si hay una versión más nueva disponible.
    """
    _validate_platform(platform)
    latest = _latest_version(platform)
    has_update = _version_tuple(latest) > _version_tuple(current_version)
    url = _download_url(request, platform, latest) if has_update else None
    return {
        "status": "ok",
        "data": {
            "has_update":      has_update,
            "current_version": current_version,
            "latest_version":  latest,
            "download_url":    url,
        }
    }

@router.get("/latest/{platform}", summary="Info de la última versión")
def get_latest(platform: str, request: Request):
    """Devuelve la versión más reciente y su URL sin comparar."""
    _validate_platform(platform)
    latest = _latest_version(platform)
    return {
        "status": "ok",
        "data": {
            "version":      latest,
            "download_url": _download_url(request, platform, latest),
        }
    }

# ── Endpoints admin ───────────────────────────────────────────────────────────

from fastapi import BackgroundTasks

@router.post("/upload/{platform}/{version}", summary="Subir nueva versión (admin)")
async def upload_version(
    platform: str,
    version:  str,
    background_tasks: BackgroundTasks,
    file:     UploadFile = File(...),
    user=Depends(get_current_user),
):
    """
    Recibe el binario (launcher.exe / app.apk / minebridge.jar) vía multipart/form-data,
    lo guarda en static/versions/{platform}/{version}/
    y actualiza el puntero en versions.json automáticamente.

    El empaquetador local llama este endpoint — sin SCP, sin git.
    Si la carpeta no existe, la crea automáticamente.
    """
    _validate_platform(platform)
    _validate_version(version)

    dest_dir  = os.path.join(_BASE_DIR, platform, version)
    filename  = _PLATFORM_FILE[platform]
    dest_path = os.path.join(dest_dir, filename)

    # Auto-crear carpeta si no existe (con log explícito)
    if not os.path.isdir(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)
        print(f"[upload] Carpeta creada: {dest_dir}")
    else:
        print(f"[upload] Usando carpeta existente: {dest_dir}")

    # Stream al disco en chunks de 1 MB
    print(f"[upload] Guardando {filename} en {dest_dir}...")
    try:
        with open(dest_path, "wb") as out:
            while chunk := await file.read(1024 * 1024):
                out.write(chunk)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando archivo: {e}")

    size_mb = os.path.getsize(dest_path) / 1_048_576
    print(f"[upload] Guardado OK: {filename} ({size_mb:.1f} MB)")

    # Actualizar puntero
    data = _load()
    old_pointer = data.get(platform, "ninguno")
    data[platform] = version
    _save(data)
    print(f"[upload] Puntero {platform}: {old_pointer} → {version}")

    # Auto-update task para el server mod
    if platform == "modserver":
        background_tasks.add_task(_apply_server_mod_update, dest_path)

    return {
        "status":  "ok",
        "message": f"{platform} v{version} publicado ({size_mb:.1f} MB)",
        "data": {
            "platform":        platform,
            "version":         version,
            "filename":        filename,
            "size_mb":         round(size_mb, 2),
            "pointer_updated": True,
            "previous_version": old_pointer,
        }
    }

class SetVersionBody(BaseModel):
    version: str

@router.put("/set/{platform}", summary="Apuntar a versión ya subida (admin)")
def set_version(platform: str, body: SetVersionBody, user=Depends(get_current_user)):
    """
    Actualiza el puntero en versions.json.
    Si la versión es la misma que la actual, lo fuerza igual
    (útil para reemplazar el binario del día sin cambiar número de versión).
    La carpeta y el archivo pueden no existir aún si el upload aún está en proceso,
    por eso no validamos la existencia del archivo.
    """
    _validate_platform(platform)
    _validate_version(body.version)
    data = _load()
    old = data.get(platform, "ninguno")
    data[platform] = body.version
    _save(data)
    action = "actualizado" if old != body.version else "re-confirmado (mismo número, nuevo binario)"
    return {"status": "ok", "message": f"Puntero {platform}: {old} → {body.version} ({action})", "data": data}


@router.get("/list/{platform}", summary="Listar versiones disponibles (admin)")
def list_versions(platform: str, user=Depends(get_current_user)):
    """Lista versiones en disco con flag is_current y has_file."""
    _validate_platform(platform)
    folder = os.path.join(_BASE_DIR, platform)
    os.makedirs(folder, exist_ok=True)
    filename = _PLATFORM_FILE[platform]
    current  = _latest_version(platform)
    versions = sorted(
        [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d))],
        key=_version_tuple
    )
    return {
        "status": "ok",
        "data": {
            "platform":        platform,
            "current_pointer": current,
            "available": [
                {
                    "version":    v,
                    "has_file":   os.path.exists(os.path.join(folder, v, filename)),
                    "is_current": v == current,
                }
                for v in versions
            ],
        }
    }
