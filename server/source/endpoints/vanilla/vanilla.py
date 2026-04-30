import requests
import json
from typing import List, Dict, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

# ==========================================
# 1. MODELOS DE DATOS (MOJANG)
# ==========================================

class VersionEntry(BaseModel):
    id: str
    type: str  # 'release' o 'snapshot'
    url: str   # URL para obtener los detalles específicos (incluida la descarga)
    time: datetime
    releaseTime: datetime

class LatestVersions(BaseModel):
    release: str
    snapshot: str

class MojangManifest(BaseModel):
    latest: LatestVersions
    versions: List[VersionEntry]

# Modelos para el detalle de la versión (Paso 2)
class DownloadInfo(BaseModel):
    sha1: str
    size: int
    url: str

class VersionDownloads(BaseModel):
    # Usamos Optional porque versiones muy antiguas pueden no tener server
    server: Optional[DownloadInfo] = None 
    client: Optional[DownloadInfo] = None

class VersionPackage(BaseModel):
    downloads: VersionDownloads

# Modelo final unificado
class FinalVanillaDownloadData(BaseModel):
    project: str = "Vanilla (Mojang)"
    version: str
    type: str
    filename: str
    filesize_bytes: int
    sha1: str
    download_url: str

# ==========================================
# 2. CLIENTE API (LÓGICA MOJANG)
# ==========================================

class VanillaClient:
    def __init__(self):
        self.manifest_url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
        self.session = requests.Session()

    def _get_manifest(self) -> MojangManifest:
        """Obtiene la lista maestra de versiones."""
        try:
            response = self.session.get(self.manifest_url)
            response.raise_for_status()
            return MojangManifest(**response.json())
        except Exception as e:
            raise RuntimeError(f"Error contactando a Mojang: {e}")

    def _get_version_package(self, url: str) -> VersionPackage:
        """Obtiene los detalles técnicos (descargas) de una versión específica."""
        response = self.session.get(url)
        response.raise_for_status()
        # Mojang devuelve un JSON complejo, solo nos importa 'downloads' por ahora
        data = response.json()
        return VersionPackage(downloads=data.get("downloads", {}))

    # ==========================================
    # FUNCION PRINCIPAL DE "BACKEND"
    # ==========================================

    def obtener_datos_descarga(self, version_id: str = "latest", type_preference: str = "release") -> str:
        """
        Orquesta el proceso para Vanilla:
        1. Obtiene el manifiesto.
        2. Resuelve la versión (ID específico o 'latest' según preferencia).
        3. Busca la URL del paquete de esa versión.
        4. Descarga el paquete y extrae la info del server.jar.
        """
        try:
            # 1. Obtener Manifiesto
            manifest = self._get_manifest()
            
            target_id = ""
            target_entry: Optional[VersionEntry] = None

            # 2. Resolver ID de versión
            if version_id == "latest":
                if type_preference == "snapshot":
                    target_id = manifest.latest.snapshot
                else:
                    target_id = manifest.latest.release
            else:
                target_id = version_id

            # 3. Buscar la entrada en la lista
            # (Optimizacion: La lista está ordenada por fecha, pero iteramos para estar seguros)
            for entry in manifest.versions:
                if entry.id == target_id:
                    target_entry = entry
                    break
            
            if not target_entry:
                raise ValueError(f"La versión '{target_id}' no existe en el manifiesto oficial de Mojang.")

            # 4. Obtener detalles de descarga (Paso 2 de la API)
            package_details = self._get_version_package(target_entry.url)
            
            if not package_details.downloads.server:
                raise ValueError(f"La versión {target_id} no tiene un archivo 'server.jar' disponible para descarga pública (común en versiones muy antiguas).")

            server_info = package_details.downloads.server

            # 5. Armar respuesta
            resultado = FinalVanillaDownloadData(
                version=target_id,
                type=target_entry.type,
                filename="server.jar", # Mojang siempre lo llama server.jar en la URL interna a veces, pero lo estandarizamos
                filesize_bytes=server_info.size,
                sha1=server_info.sha1,
                download_url=server_info.url
            )

            return resultado.model_dump_json(indent=4)

        except Exception as e:
            return json.dumps({"error": str(e), "success": False})

