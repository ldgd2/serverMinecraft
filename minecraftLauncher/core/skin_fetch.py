"""
core/skin_fetch.py
Fetches a premium player's skin directly from the Mojang API using their UUID.
Also handles the download and caching of the skin PNG locally.
"""
import os
import json
import base64
import threading
import requests
from typing import Callable, Optional


_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "skin_cache")
_PROFILE_URL = "https://sessionserver.mojang.com/session/minecraft/profile/{uuid}"


def _cache_path(uuid: str) -> str:
    os.makedirs(_CACHE_DIR, exist_ok=True)
    clean = uuid.replace("-", "")
    return os.path.join(_CACHE_DIR, f"{clean}.png")


def fetch_skin_from_mojang(uuid: str, on_done: Callable[[Optional[str]], None], force: bool = False) -> None:
    """
    Fetch the skin PNG for a premium player by UUID.
    Calls on_done(local_path) on success, or on_done(None) on failure.
    Runs in a background thread.
    """
    def _fetch():
        if not uuid:
            on_done(None)
            return

        # Check local cache first (1-hour) 
        cache = _cache_path(uuid)
        if not force and os.path.exists(cache):
            age = os.path.getmtime(cache)
            import time
            if time.time() - age < 3600:  # 1 hour cache
                on_done(cache)
                return

        try:
            url = _PROFILE_URL.format(uuid=uuid.replace("-", ""))
            resp = requests.get(url, timeout=8)
            resp.raise_for_status()
            profile = resp.json()

            # Decode TEXTURES property from base64
            props = profile.get("properties", [])
            texture_b64 = None
            for prop in props:
                if prop.get("name") == "textures":
                    texture_b64 = prop["value"]
                    break

            if not texture_b64:
                on_done(None)
                return

            texture_json = json.loads(base64.b64decode(texture_b64 + "==").decode("utf-8"))
            skin_url = texture_json.get("textures", {}).get("SKIN", {}).get("url")

            if not skin_url:
                on_done(None)
                return

            # Download the PNG
            img_resp = requests.get(skin_url, timeout=8)
            img_resp.raise_for_status()

            with open(cache, "wb") as f:
                f.write(img_resp.content)

            on_done(cache)

        except Exception as e:
            print(f"[SkinFetch] Error fetching skin for {uuid}: {e}")
            # Return cached even if stale
            if os.path.exists(cache):
                on_done(cache)
            else:
                on_done(None)

    threading.Thread(target=_fetch, daemon=True).start()


def get_cached_skin(uuid: str) -> Optional[str]:
    """Return the cached skin path synchronously, or None if not cached."""
    if not uuid:
        return None
    cache = _cache_path(uuid)
    return cache if os.path.exists(cache) else None


def upload_skin_to_mojang(skin_path: str, access_token: str, variant: str = "classic") -> dict:
    """
    Upload a skin PNG to Mojang's profile service.
    Returns {"status": "OK"} or {"status": "ERROR", "message": "..."}.
    """
    if not skin_path or not os.path.exists(skin_path):
        return {"status": "ERROR", "message": "Archivo de skin no encontrado."}
    if not access_token:
        return {"status": "ERROR", "message": "No hay token de acceso válido (no estás logeado como premium)."}

    url = "https://api.minecraftservices.com/minecraft/profile/skins"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        with open(skin_path, "rb") as f:
            files = {"file": (os.path.basename(skin_path), f, "image/png")}
            data  = {"variant": variant}
            resp  = requests.post(url, headers=headers, files=files, data=data, timeout=15)

        if resp.status_code in (200, 204):
            return {"status": "OK", "message": "✓ Skin subida correctamente a Mojang."}
        else:
            try:
                body = resp.json()
                msg  = body.get("errorMessage") or body.get("error") or f"HTTP {resp.status_code}"
            except Exception:
                msg = f"HTTP {resp.status_code}"
            return {"status": "ERROR", "message": f"Error Mojang: {msg}"}

    except requests.exceptions.ConnectionError:
        return {"status": "ERROR", "message": "Sin conexión a Internet."}
    except requests.exceptions.Timeout:
        return {"status": "ERROR", "message": "Tiempo de espera agotado."}
    except Exception as e:
        return {"status": "ERROR", "message": f"Error inesperado: {str(e)}"}
