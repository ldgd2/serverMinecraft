import requests
import json
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field

# ==========================================
# 1. MODELOS DE DATOS (SCHEMAS V2)
# ==========================================

class Download(BaseModel):
    name: str
    sha256: str
    size: Optional[int] = 0
    url: Optional[str] = None 

class Commit(BaseModel):
    author: Optional[str] = None
    email: Optional[str] = None
    message: str
    commit: str
    time: Optional[datetime] = None

class Project(BaseModel):
    project_id: str
    project_name: str
    version_groups: List[str] = []
    versions: List[str] = []

class VersionDetails(BaseModel):
    project_id: str
    project_name: str
    version: str
    builds: List[int]

class BuildResponse(BaseModel):
    project_id: str
    project_name: str
    version: str
    build: int
    time: datetime
    channel: str
    promoted: bool
    changes: List[Commit]
    downloads: Dict[str, Download]

# Modelo final simplificado para entregar al frontend/sistema
class FinalDownloadData(BaseModel):
    project: str
    version: str
    build: int
    filename: str
    filesize_bytes: int
    sha256: str
    download_url: str
    timestamp: datetime

# ==========================================
# 2. CLIENTE API (LÓGICA)
# ==========================================

class PaperMCClient:
    def __init__(self, base_url: str = "https://api.papermc.io"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def _get(self, path: str) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    # --- Endpoints Básicos ---

    def get_project_details(self, project_id: str) -> Project:
        data = self._get(f"/v2/projects/{project_id}")
        return Project(**data)

    def get_version_details(self, project_id: str, version: str) -> VersionDetails:
        data = self._get(f"/v2/projects/{project_id}/versions/{version}")
        return VersionDetails(**data)

    def get_build_details(self, project_id: str, version: str, build_id: int) -> BuildResponse:
        data = self._get(f"/v2/projects/{project_id}/versions/{version}/builds/{build_id}")
        return BuildResponse(**data)

    def _build_url(self, project_id: str, version: str, build_id: int, file_name: str) -> str:
        return (f"{self.base_url}/v2/projects/{project_id}"
                f"/versions/{version}/builds/{build_id}/downloads/{file_name}")

    # ==========================================
    # FUNCION PRINCIPAL DE "BACKEND"
    # Captura datos, resuelve automáticos y devuelve JSON
    # ==========================================
    
    def obtener_datos_descarga(self, project_id: str, version: str = "latest", build_id: Union[int, str] = "latest") -> str:
        """
        Orquesta todo el proceso:
        1. Si la versión es 'latest', busca la última disponible.
        2. Si el build es 'latest', busca el último disponible.
        3. Obtiene los metadatos y construye la URL.
        4. Retorna todo en formato JSON string.
        """
        try:
            # 1. Resolver Versión
            if version == "latest":
                proj_data = self.get_project_details(project_id)
                if not proj_data.versions:
                    raise ValueError(f"El proyecto {project_id} no tiene versiones.")
                real_version = proj_data.versions[-1]
            else:
                real_version = version

            # 2. Resolver Build
            if build_id == "latest":
                ver_data = self.get_version_details(project_id, real_version)
                if not ver_data.builds:
                    raise ValueError(f"La versión {real_version} no tiene builds.")
                real_build = ver_data.builds[-1]
            else:
                real_build = int(build_id)

            # 3. Obtener detalles del archivo
            build_info = self.get_build_details(project_id, real_version, real_build)
            
            # Buscar la descarga principal (application)
            if "application" not in build_info.downloads:
                raise ValueError("No se encontró una descarga tipo 'application' en este build.")
            
            app_data = build_info.downloads["application"]
            final_url = self._build_url(project_id, real_version, real_build, app_data.name)

            # 4. Armar respuesta limpia
            resultado = FinalDownloadData(
                project=build_info.project_name,
                version=real_version,
                build=real_build,
                filename=app_data.name,
                filesize_bytes=app_data.size,
                sha256=app_data.sha256,
                download_url=final_url,
                timestamp=build_info.time
            )
            
            # Devolver JSON
            return resultado.model_dump_json(indent=4)

        except Exception as e:
            # En caso de error, devolvemos un JSON de error
            return json.dumps({"error": str(e), "success": False})

