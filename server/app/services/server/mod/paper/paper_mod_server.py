import requests
from bs4 import BeautifulSoup
import re
import os
import sys
import shutil

class PaperPluginManager:
    def __init__(self, base_path="servers"):
        self.base_url = "https://hangar.papermc.io"
        self.base_path = base_path
        # Headers para simular un navegador real y evitar bloqueos simples
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def obtener_url_categoria(self, tipo, query=None):
        """Genera la URL basada en los filtros solicitados"""
        # Hangar filter params
        # query e.g. ?q=essentials&platform=PAPER
        base_params = "?platform=PAPER"
        
        # Mapping sort types to Hangar URL params
        # Note: Hangar URLs might differ slightly, trying to match user provided logic
        urls = {
            "estrellas": f"{base_params}&sort=-stars",
            "descargas_recientes": f"{base_params}&sort=-recent_downloads",
            "mas_descargados": f"{base_params}&sort=-downloads",
            "actualizados": f"{base_params}&sort=-updated",
            "nuevos": f"{base_params}&sort=-newest",
        }

        if tipo == "buscar" and query:
            # Reemplaza espacios con + para la URL
            query_formatted = query.replace(" ", "+")
            return f"{self.base_url}/{base_params}&q={query_formatted}"
        
        # Default to stars if type not found, or use specific category URL logic
        # user code: return f"{self.base_url}/{urls.get(tipo, urls['estrellas'])}"
        # But Hangar base URL + query params is usually how search works.
        # If accessing the main list: https://hangar.papermc.io/?platform=PAPER...
        
        suffix = urls.get(tipo, urls['estrellas'])
        return f"{self.base_url}/{suffix}"

    def obtener_html(self, url):
        try:
            print(f"[*] Conectando a: {url} ...")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"[!] Error al conectar: {e}")
            return None

    def parsear_lista_resultados(self, html_content):
        """
        Analiza la página de búsqueda/categoría para encontrar enlaces a mods.
        Busca patrones tipo href="/Autor/Proyecto"
        """
        if not html_content: return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        mods_encontrados = []
        
        # Estrategia: Buscar enlaces que parezcan proyectos (Autor/Nombre)
        # Filtramos enlaces de sistema (auth, admin, etc.)
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Regex: /Autor/Proyecto (excluyendo rutas de sistema)
            if re.match(r'^/[^/]+/[^/]+$', href):
                parts = href.split('/')
                # parts[0] is empty, parts[1] is author, parts[2] is project
                if len(parts) >= 3 and parts[1] not in ['auth', 'admin', 'api', 'linkout', 'favicon', '_nuxt', 'notifications', 'tools']:
                    author = parts[1]
                    name = parts[2]
                    url_completa = f"{self.base_url}{href}"
                    
                    # Try to find description or other metadata if possible (optional enhancement)
                    # For now stick to user logic
                    
                    # Evitar duplicados
                    if not any(m['url'] == url_completa for m in mods_encontrados):
                        mods_encontrados.append({
                            'author': author,
                            'name': name,
                            'url': url_completa,
                            'ruta_relativa': href
                        })
        
        return mods_encontrados

    def parsear_detalle_mod(self, html_content):
        """
        Extrae la información detallada y el link de descarga (Lógica mejorada)
        """
        if not html_content: return {}
        
        soup = BeautifulSoup(html_content, 'html.parser')
        data = {}

        # 1. Nombre y Autor (Intento vía JSON-LD primero)
        script_json = soup.find('script', attrs={'type': 'application/ld+json', 'data-hid': 'breadcrumb'})
        if script_json:
            try:
                import json
                b_data = json.loads(script_json.string)
                if len(b_data.get('itemListElement', [])) > 2:
                    data['author'] = b_data['itemListElement'][1]['name']
                    data['name'] = b_data['itemListElement'][2]['name']
            except:
                pass
        
        if 'name' not in data:
            h1 = soup.find('h1')
            data['name'] = h1.text.strip() if h1 else "Desconocido"

        # 2. Enlace de descarga (.jar)
        # Buscamos enlaces al CDN de hangar
        # Hangar download buttons usually go to /api/v1/projects/.../versions/.../download
        # Or sometimes they are just links matching the regex
        download_link = soup.find('a', href=re.compile(r'hangarcdn\.papermc\.io/plugins/.+\.jar'))
        
        # Fallback: look for "Download" button that might link to a version page or direct download
        if not download_link:
             # Try finding the "Download" button in the header
             dl_btn = soup.find('a', string=re.compile(r'Download', re.I))
             if dl_btn and 'href' in dl_btn.attrs:
                 # If it points to versions page, we might need to drill down, but let's see
                 pass

        if download_link:
            data['download_url'] = download_link['href']
            # Extraer versión de la URL
            v_match = re.search(r'/versions/([^/]+)/', data['download_url'])
            data['version'] = v_match.group(1).replace('%2B', '+') if v_match else "latest"
        else:
            data['download_url'] = None

        # Add description for UI
        # meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            data['description'] = meta_desc.get('content')
            
        return data
    
    def get_plugin_versions(self, project_owner, project_slug):
        """
        Uses Hangar API to get versions for a project to support version filtering.
        This provides better reliability than scraping for downloads.
        """
        api_url = f"https://hangar.papermc.io/api/v1/projects/{project_owner}/{project_slug}/versions"
        try:
            resp = requests.get(api_url, headers=self.headers)
            if resp.status_code == 200:
                return resp.json().get('result', [])
        except: pass
        return []

    def descargar_e_instalar(self, mod_data, nombre_servidor):
        """
        Descarga el archivo y lo guarda en servers/nombreServidor/plugins
        """
        if not mod_data.get('download_url'):
            print(f"[!] No se encontró enlace de descarga directa (.jar) para {mod_data.get('name')}")
            return False, "No download URL found"

        # Ruta destino: servers/nombreServidor/plugins
        directorio_plugins = os.path.join(self.base_path, nombre_servidor, "plugins")
        
        # Crear directorios si no existen
        os.makedirs(directorio_plugins, exist_ok=True)

        # Nombre del archivo
        version_str = mod_data.get('version', 'latest')
        nombre_clean = re.sub(r'[<>:"/\\|?*]', '', mod_data['name'])
        nombre_archivo = f"{nombre_clean}-{version_str}.jar"
        
        ruta_final = os.path.join(directorio_plugins, nombre_archivo)

        print(f"[*] Descargando {mod_data['name']}...")
        print(f"    URL: {mod_data['download_url']}")
        
        try:
            r = requests.get(mod_data['download_url'], stream=True, headers=self.headers)
            r.raise_for_status()
            
            with open(ruta_final, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"[ok] Instalado en: {ruta_final}")
            return True, f"Instalado correctamente: {nombre_archivo}"
            
        except Exception as e:
            print(f"[!] Error descargando archivo: {e}")
            return False, str(e)

    def listar_plugins_instalados(self, nombre_servidor):
        """
        Escanea recursivamente la carpeta plugins Y la carpeta raíz del servidor
        buscando archivos .jar.
        Retorna rutas relativas al directorio del servidor.
        """
        server_path = os.path.join(self.base_path, nombre_servidor)
        if not os.path.exists(server_path):
            return []
            
        plugins = []
        
        # 1. Escanear carpeta 'plugins' (Recursivo)
        plugins_path = os.path.join(server_path, "plugins")
        if os.path.exists(plugins_path):
            for root, dirs, files in os.walk(plugins_path):
                for f in files:
                    if f.endswith('.jar'):
                        full_path = os.path.join(root, f)
                        # Calcular ruta relativa para mostrar en frontend (ej: plugins/WorldEdit.jar)
                        rel_path = os.path.relpath(full_path, server_path).replace("\\", "/")
                        size_mb = os.path.getsize(full_path) / (1024 * 1024)
                        
                        plugins.append({
                            'filename': rel_path,
                            'name_only': f,
                            'location': 'plugins',
                            'size': f"{size_mb:.2f} MB"
                        })

        # 2. Escanear raíz del servidor (No recursivo, solo archivos sueltos)
        # Esto es para detectar esos plugins "raros" que mencionaste.
        for item in os.listdir(server_path):
            full_path = os.path.join(server_path, item)
            if os.path.isfile(full_path) and item.endswith('.jar'):
                # Intentamos no listar el propio paper.jar/server.jar si es obvio, 
                # pero mejor mostramos todo y que el usuario decida.
                size_mb = os.path.getsize(full_path) / (1024 * 1024)
                plugins.append({
                    'filename': item, # Está en la raíz
                    'name_only': item,
                    'location': 'root',
                    'size': f"{size_mb:.2f} MB",
                    'warning': True # Flag para indicar cuidado en frontend
                })
                
        return plugins

    def eliminar_plugin(self, nombre_servidor, rel_path):
        """
        Elimina el archivo .jar Y busca recursivamente su carpeta de configuración asociada
        tanto en 'plugins' como en la raíz del servidor.
        """
        # Validación de seguridad: Evitar salir del directorio del server
        if '..' in rel_path:
            return False, "Ruta inválida detectada."

        from pathlib import Path
        server_path = Path(os.path.join(self.base_path, nombre_servidor)).resolve()
        file_path = Path(os.path.join(server_path, rel_path)).resolve()

        # Doble chequeo de seguridad
        try:
            file_path.relative_to(server_path)
        except ValueError:
             return False, "Acceso denegado fuera del servidor."

        if not os.path.exists(file_path):
            return False, "Archivo no encontrado."

        try:
            filename = os.path.basename(rel_path)
            msg = f"Eliminado: {filename}"
            
            # --- 1. Eliminar el archivo .jar Principal ---
            os.remove(file_path)

            # --- Identificar el nombre "base" del plugin ---
            # Estrategia: "BlueMap-3.2.jar" -> "BlueMap"
            # 1. Quitar extensión
            base_name = os.path.splitext(filename)[0]
            
            # 2. Intentar obtener nombre limpio cortando en versiones (-, v, números)
            # Ej: Plugin-1.2.jar -> Plugin
            clean_name_match = re.match(r'^([a-zA-Z0-9_\s]+?)[-\s]*v?\d.*', base_name)
            clean_name = clean_name_match.group(1) if clean_name_match else base_name
            clean_name = clean_name.strip()

            candidates = {base_name, clean_name}
            # Evitar nombres vacíos o super cortos peligrosos
            candidates = {c for c in candidates if len(c) > 2}

            # --- Carpetas protegidas (NO TOCAR) ---
            protected_folders = {
                'logs', 'crash-reports', 'world', 'world_nether', 'world_the_end', 
                'plugins', 'libraries', 'versions', 'cache', 'bundler', 'config',
                'banned-ips.json', 'banned-players.json', 'ops.json', 'server.properties', 
                'whitelist.json', 'usercache.json', 'eula.txt'
            }

            def safe_remove_dir(target_path, location_desc):
                nonlocal msg
                t_name = os.path.basename(target_path)
                if t_name.lower() in protected_folders:
                    return # Skip protected
                
                if os.path.exists(target_path) and os.path.isdir(target_path):
                     shutil.rmtree(target_path)
                     msg += f" + Carpeta {location_desc} '{t_name}'"

            # --- 2. Buscar carpetas en 'plugins/' ---
            # Generalmente: plugins/EssentialsX para EssentialsX.jar
            plugins_dir = os.path.join(server_path, "plugins")
            if os.path.exists(plugins_dir):
                for cand in candidates:
                     target = os.path.join(plugins_dir, cand)
                     safe_remove_dir(target, "plugin")

            # --- 3. Buscar carpetas en 'server_root/' ---
            # Algunos plugins (o mods) crean carpetas en la raíz
            # Ej: plugins/BlueMap.jar -> server_root/BlueMap/
            for cand in candidates:
                 target = os.path.join(server_path, cand)
                 # Solo borrar si NO es la propia carpeta plugins, y no está protegida
                 if target != plugins_dir:
                     safe_remove_dir(target, "root")

            return True, msg

        except Exception as e:
            return False, f"Error al eliminar: {str(e)}"
