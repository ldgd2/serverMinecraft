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
    return {"launcher": "1.0.0", "app": "1.0.0"}

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
        raise HTTPException(status_code=400, detail="platform must be 'launcher' or 'app'")

def _validate_version(version: str):
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        raise HTTPException(status_code=422, detail="version must be X.Y.Z format")

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

@router.post("/upload/{platform}/{version}", summary="Subir nueva versión (admin)")
async def upload_version(
    platform: str,
    version:  str,
    file:     UploadFile = File(...),
    user=Depends(get_current_user),
):
    """
    Recibe el binario (launcher.exe / app.apk) vía multipart/form-data,
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
    """Cambia el puntero sin subir archivo (la versión ya debe existir en disco)."""
    _validate_platform(platform)
    dest = os.path.join(_BASE_DIR, platform, body.version, _PLATFORM_FILE[platform])
    if not os.path.exists(dest):
        raise HTTPException(
            status_code=404,
            detail=f"No existe {_PLATFORM_FILE[platform]} en versions/{platform}/{body.version}/"
        )
    data = _load()
    data[platform] = body.version
    _save(data)
    return {"status": "ok", "message": f"Puntero {platform} → {body.version}", "data": data}

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
