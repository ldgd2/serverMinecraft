import requests
import json
from typing import Dict, Optional
from datetime import datetime
from pydantic import BaseModel

# ==========================================
# 1. MODELOS DE DATOS
# ==========================================

class ForgePromotionsResponse(BaseModel):
    homepage: str
    promos: Dict[str, str]

class FinalForgeDownloadData(BaseModel):
    project: str = "Forge"
    mc_version: str
    forge_version: str
    type: str # 'recommended', 'latest', o 'custom'
    filename: str
    download_url: str
    note: str

# ==========================================
# 2. CLIENTE API (LÓGICA FORGE)
# ==========================================

class ForgeClient:
    def __init__(self):
        # URL oficial para obtener las versiones
        self.promotions_url = "https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json"
        self.maven_base_url = "https://maven.minecraftforge.net/net/minecraftforge/forge"
        self.session = requests.Session()
        # Cabeceras para parecer un navegador normal y evitar bloqueos
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def _get_promotions(self) -> ForgePromotionsResponse:
        """Descarga el JSON de promociones (lista de versiones)"""
        try:
            response = self.session.get(self.promotions_url)
            response.raise_for_status()
            return ForgePromotionsResponse(**response.json())
        except Exception as e:
            raise RuntimeError(f"Error obteniendo promociones de Forge: {e}")

    def _build_maven_url(self, mc_ver: str, forge_ver: str) -> str:
        """
        Construye la URL directa al repositorio Maven, saltando AdFocus.
        Formato estándar: 
        Base + / {mc_ver}-{forge_ver} / forge-{mc_ver}-{forge_ver}-installer.jar
        """
        # Nota: En versiones muy antiguas (pre-1.6), el formato cambiaba, 
        # pero para servidores modernos (1.7.10+) este es el estándar.
        
        file_name = f"forge-{mc_ver}-{forge_ver}-installer.jar"
        # La carpeta en el repo suele ser "MC-FORGE"
        path = f"{mc_ver}-{forge_ver}"
        
        return f"{self.maven_base_url}/{path}/{file_name}"

    # ==========================================
    # FUNCION PRINCIPAL DE "BACKEND"
    # ==========================================

    def obtener_datos_descarga(self, mc_version: str, preference: str = "recommended") -> str:
        """
        Busca la versión de Forge para la versión de Minecraft dada.
        
        :param mc_version: Versión de Minecraft (ej. '1.20.1')
        :param preference: 'recommended' (estable) o 'latest' (última beta)
        :return: JSON string con los datos de descarga
        """
        try:
            # 1. Obtener datos crudos
            promo_data = self._get_promotions()
            promos = promo_data.promos

            # 2. Buscar la clave correcta (ej. '1.20.1-recommended')
            key_rec = f"{mc_version}-recommended"
            key_lat = f"{mc_version}-latest"
            
            selected_ver = None
            selected_type = ""

            # Lógica de selección:
            if preference == "recommended":
                if key_rec in promos:
                    selected_ver = promos[key_rec]
                    selected_type = "recommended"
                elif key_lat in promos:
                    # Fallback: Si no hay recomendada, usamos la latest pero avisamos
                    selected_ver = promos[key_lat]
                    selected_type = "latest (fallback)"
                else:
                    raise ValueError(f"No hay versiones de Forge para Minecraft {mc_version}")
            
            elif preference == "latest":
                if key_lat in promos:
                    selected_ver = promos[key_lat]
                    selected_type = "latest"
                elif key_rec in promos:
                    selected_ver = promos[key_rec]
                    selected_type = "recommended (fallback)"
                else:
                    raise ValueError(f"No hay versiones de Forge para Minecraft {mc_version}")
            
            else:
                # Caso borde: Se pide una versión específica de Forge directamente?
                # Por ahora asumimos que 'preference' es el tipo de build.
                raise ValueError("Preferencia inválida. Use 'recommended' o 'latest'.")

            # 3. Construir URL limpia (Directa Maven)
            final_url = self._build_maven_url(mc_version, selected_ver)
            filename = f"forge-{mc_version}-{selected_ver}-installer.jar"

            # 4. Retornar Resultado
            resultado = FinalForgeDownloadData(
                mc_version=mc_version,
                forge_version=selected_ver,
                type=selected_type,
                filename=filename,
                download_url=final_url,
                note="URL directa al repositorio Maven (AdFocus omitido)."
            )

            return resultado.model_dump_json(indent=4)

        except Exception as e:
            return json.dumps({"error": str(e), "success": False})
