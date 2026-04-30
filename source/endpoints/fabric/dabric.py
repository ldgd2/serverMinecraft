import requests
import json
from typing import List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

# ==========================================
# 1. MODELOS DE DATOS (SCHEMAS FABRIC)
# ==========================================

class FabricGameVersion(BaseModel):
    version: str
    stable: bool

class FabricLoaderInfo(BaseModel):
    version: str
    stable: bool

class FabricInstallerInfo(BaseModel):
    version: str
    url: str
    stable: bool

# Modelo final para entregar al frontend/sistema
class FinalFabricDownloadData(BaseModel):
    project: str = "Fabric"
    game_version: str
    loader_version: str
    installer_version: str
    filename: str
    download_url: str
    note: str

# ==========================================
# 2. CLIENTE API (LÓGICA)
# ==========================================

class FabricClient:
    def __init__(self, base_url: str = "https://meta.fabricmc.net"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def _get(self, path: str) -> List[dict]:
        """Fabric devuelve listas directamente en la raíz del JSON usualmente"""
        url = f"{self.base_url}{path}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    # --- Endpoints de Metadatos ---

    def get_game_versions(self) -> List[FabricGameVersion]:
        """GET /v2/versions/game"""
        data = self._get("/v2/versions/game")
        return [FabricGameVersion(**item) for item in data]

    def get_loader_versions(self, game_version: str) -> List[FabricLoaderInfo]:
        """GET /v2/versions/loader/{game_version}"""
        # Nota: Fabric permite consultar loaders compatibles con una versión específica
        data = self._get(f"/v2/versions/loader/{game_version}")
        # La respuesta contiene un objeto 'loader', extraemos esa parte
        return [FabricLoaderInfo(**item['loader']) for item in data]

    def get_installer_versions(self) -> List[FabricInstallerInfo]:
        """GET /v2/versions/installer"""
        data = self._get("/v2/versions/installer")
        return [FabricInstallerInfo(**item) for item in data]

    # --- Generación de URL ---

    def _build_server_url(self, game: str, loader: str, installer: str) -> str:
        """
        Construye la URL directa del JAR del servidor.
        GET /v2/versions/loader/{game_version}/{loader_version}/{installer_version}/server/jar
        """
        return (f"{self.base_url}/v2/versions/loader/"
                f"{game}/{loader}/{installer}/server/jar")

    # ==========================================
    # FUNCION PRINCIPAL DE "BACKEND"
    # ==========================================

    def obtener_datos_descarga(
        self, 
        game_version: str = "latest", 
        loader_version: str = "latest", 
        installer_version: str = "latest"
    ) -> str:
        """
        Orquesta el proceso para Fabric:
        1. Resuelve Game Version (si es 'latest', busca la última estable).
        2. Resuelve Loader Version (si es 'latest', busca el último estable para ese juego).
        3. Resuelve Installer Version (si es 'latest', busca el último estable).
        4. Genera el JSON final.
        """
        try:
            # 1. Resolver Versión del Juego
            all_games = self.get_game_versions()
            if game_version == "latest":
                # Filtramos solo estables y tomamos la primera (la API las devuelve ordenadas)
                stable_games = [g for g in all_games if g.stable]
                if not stable_games:
                    raise ValueError("No se encontraron versiones estables de Minecraft.")
                real_game_ver = stable_games[0].version
            else:
                # Validamos que la versión exista
                if not any(g.version == game_version for g in all_games):
                    raise ValueError(f"La versión de juego {game_version} no existe en Fabric.")
                real_game_ver = game_version

            # 2. Resolver Loader
            all_loaders = self.get_loader_versions(real_game_ver)
            if loader_version == "latest":
                stable_loaders = [l for l in all_loaders if l.stable]
                if not stable_loaders:
                    # Fallback a inestable si no hay estable (raro, pero posible en snapshots)
                    real_loader_ver = all_loaders[0].version
                else:
                    real_loader_ver = stable_loaders[0].version
            else:
                real_loader_ver = loader_version

            # 3. Resolver Installer
            all_installers = self.get_installer_versions()
            if installer_version == "latest":
                stable_installers = [i for i in all_installers if i.stable]
                if not stable_installers:
                     real_installer_ver = all_installers[0].version
                else:
                    real_installer_ver = stable_installers[0].version
            else:
                real_installer_ver = installer_version

            # 4. Construir URL y Filename
            final_url = self._build_server_url(real_game_ver, real_loader_ver, real_installer_ver)
            
            # Fabric no devuelve metadatos del archivo final (tamaño/hash) antes de descargarlo 
            # en este endpoint, así que generamos el nombre estándar nosotros.
            filename_predicted = f"fabric-server-mc.{real_game_ver}-loader.{real_loader_ver}-launcher.{real_installer_ver}.jar"

            resultado = FinalFabricDownloadData(
                game_version=real_game_ver,
                loader_version=real_loader_ver,
                installer_version=real_installer_ver,
                filename=filename_predicted,
                download_url=final_url,
                note="Este enlace genera el archivo JAR directamente."
            )

            return resultado.model_dump_json(indent=4)

        except Exception as e:
            return json.dumps({"error": str(e), "success": False})

