import os
import requests
import json

class FabricModManager:
    def __init__(self, base_path="servers"):
        self.base_url = "https://api.modrinth.com/v2"
        self.base_path = base_path
        self.headers = {
            'User-Agent': 'MinecraftServerManager/1.0 (internal)'
        }

    def buscar_mods(self, query=None, version=None, sort="relevance"):
        endpoint = f"{self.base_url}/search"
        
        # FILTRO FABRIC
        # Note: Modrinth API expects facets as stringified JSON in query param if using requests params,
        # or just correct structure.
        facets = [["categories:fabric"]]
        if version:
            facets.append([f"versions:{version}"])
            
        params = {
            "query": query if query else "",
            "facets": json.dumps(facets),
            "limit": 20
        }

        if sort == "downloads": params["index"] = "downloads"
        elif sort == "newest": params["index"] = "newest"
        elif sort == "updated": params["index"] = "updated"
        else: params["index"] = "relevance"

        try:
            print(f"[*] Searching Modrinth (Fabric): {params}")
            r = requests.get(endpoint, headers=self.headers, params=params)
            r.raise_for_status()
            data = r.json()
            
            resultados = []
            for hit in data.get('hits', []):
                resultados.append({
                    'author': hit.get('author'),
                    'name': hit.get('title'),
                    'slug': hit.get('slug'),
                    'description': hit.get('description'),
                    'url': f"https://modrinth.com/mod/{hit.get('slug')}",
                    'icon': hit.get('icon_url') or "https://via.placeholder.com/64?text=Fabric",
                    'loader': 'FABRIC'
                })
            return resultados
        except Exception as e:
            print(f"[!] Modrinth API Error: {e}")
            return []

    def obtener_info_descarga(self, slug, version_mc):
        if not version_mc: return None

        endpoint = f"{self.base_url}/project/{slug}/version"
        
        # FILTRO FABRIC EN DESCARGAS
        params = {
            "loaders": json.dumps(["fabric"]),
            "game_versions": json.dumps([version_mc])
        }

        try:
            print(f"[*] Searching compatible Fabric version for {slug} on {version_mc}...")
            r = requests.get(endpoint, headers=self.headers, params=params)
            r.raise_for_status()
            versions = r.json()

            if not versions: return None
            
            target_version = versions[0]
            primary_file = next((f for f in target_version['files'] if f['primary']), target_version['files'][0])
            
            return {
                'url': primary_file['url'],
                'filename': primary_file['filename'],
                'version_name': target_version['name']
            }

        except Exception as e:
            print(f"[!] Error getting download info: {e}")
            return None

    def instalar_mod(self, server_name, download_info):
        path = os.path.join(self.base_path, server_name, "mods")
        os.makedirs(path, exist_ok=True)
        
        file_path = os.path.join(path, download_info['filename'])
        
        try:
            print(f"[*] Downloading to: {file_path}")
            r = requests.get(download_info['url'], stream=True, headers=self.headers)
            r.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True, file_path
        except Exception as e:
            return False, str(e)

    def listar_mods_instalados(self, server_name):
        server_path = os.path.join(self.base_path, server_name)
        if not os.path.exists(server_path): return []
        
        mods_list = []
        mods_path = os.path.join(server_path, "mods")
        if os.path.exists(mods_path):
            for root, dirs, files in os.walk(mods_path):
                for f in files:
                    if f.endswith('.jar'):
                        full_path = os.path.join(root, f)
                        rel_path = os.path.relpath(full_path, server_path).replace("\\", "/")
                        size_mb = os.path.getsize(full_path) / (1024 * 1024)
                        mods_list.append({
                            'filename': rel_path,
                            'name_only': f,
                            'location': 'mods',
                            'size': f"{size_mb:.2f} MB"
                        })
        return mods_list

    def eliminar_mod(self, server_name, rel_path):
        if '..' in rel_path: return False, "Invalid path."
        from pathlib import Path
        server_path = Path(os.path.join(self.base_path, server_name)).resolve()
        file_path = Path(os.path.join(server_path, rel_path)).resolve()
        
        try:
            file_path.relative_to(server_path)
        except ValueError:
             return False, "Access denied."
             
        if not os.path.exists(file_path): return False, "File not found."
        
        try:
            os.remove(file_path)
            return True, f"Deleted: {os.path.basename(rel_path)}"
        except Exception as e:
            return False, str(e)
    def get_mod_details(self, slug):
        endpoint = f"{self.base_url}/project/{slug}"
        try:
            r = requests.get(endpoint, headers=self.headers)
            r.raise_for_status()
            data = r.json()
            
            return {
                "id": data.get("id"),
                "slug": data.get("slug"),
                "title": data.get("title"),
                "description": data.get("description"),
                "body": data.get("body"), # Markdown description
                "icon_url": data.get("icon_url"),
                "issues_url": data.get("issues_url"),
                "source_url": data.get("source_url"),
                "wiki_url": data.get("wiki_url"),
                "downloads": data.get("downloads"),
                "followers": data.get("followers"),
                "categories": data.get("categories"),
                "versions": [], # We could fetch versions separately if needed
                "gallery": [g['url'] for g in data.get("gallery", [])]
            }
        except Exception as e:
            print(f"[!] Error getting mod details: {e}")
            return None
