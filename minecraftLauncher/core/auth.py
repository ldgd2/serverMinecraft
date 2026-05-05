import requests
import json
import threading
import socketserver
import http.server
import urllib.parse
from config.manager import config
import minecraft_launcher_lib

class AuthController:
    def __init__(self):
        # Usamos api_url para el backend de LiderAuth
        api_url = config.get("api_url")
        if not api_url:
             ip = config.get("server_ip") or "127.0.0.1"
             port = config.get("server_port") or 8000
             if port == 25565: # Evitar puerto por defecto de Minecraft
                  port = 8000
             api_url = f"http://{ip}:{port}/api/v1"
        self.api_url = api_url

    def login_no_premium(self, username, password):
        """
        Inicia sesión No-Premium contra el backend LiderAuth.
        Retorna un diccionario con el estado y los datos de la respuesta.
        """
        url = f"{self.api_url}/player-auth/login"
        payload = {"username": username, "password": password}
        
        try:
            print(f"[Auth] Intentando Login No-Premium en {url}...")
            respuesta = requests.post(url, json=payload, timeout=10)
            print(f"[Auth] Respuesta del servidor: {respuesta.status_code}")
            
            if respuesta.status_code == 200:
                datos = respuesta.json()
                data = datos.get("data", {})
                return {"status": "OK", "data": {
                    "username": data.get("username"),
                    "uuid": data.get("uuid"),
                    "token": data.get("access_token"),
                    "account_type": data.get("account_type"),
                }}
            
            print(f"[Auth] Error del servidor: {respuesta.text}")
            return {"status": "ERROR", "message": respuesta.json().get("detail", "Credenciales inválidas.")}

        except requests.exceptions.ConnectionError as e:
            print(f"[Auth] Error de conexión: {str(e)}")
            return {"status": "ERROR", "message": "No se pudo conectar al servidor de autenticación."}
        except Exception as e:
            print(f"[Auth] Error inesperado: {str(e)}")
            return {"status": "ERROR", "message": f"Error inesperado: {str(e)}"}

    def register_no_premium(self, username, password, birthday=None):
        """Registra un nuevo jugador No-Premium."""
        url = f"{self.api_url}/player-auth/register"
        payload = {"username": username, "password": password}
        if birthday:
            payload["birthday"] = birthday
        try:
             res = requests.post(url, json=payload, timeout=10)
             if res.status_code == 200:
                  data = res.json().get("data", {})
                  return {"status": "OK", "message": "Registrado correctamente.", "data": data}
             try: datos = res.json()
             except: datos = {}
             detail = datos.get("detail", "Error al registrar.")
             if isinstance(detail, list):
                  detail = detail[0].get("msg", "Error de validación.")
             return {"status": "ERROR", "message": detail}
        except Exception as e:
             return {"status": "ERROR", "message": str(e)}

    def enviar_nuevo_nombre(self, nombre_temporal, password, nuevo_nombre):
        """Envía la elección del nuevo nombre en caso de colisión de Nick."""
        url = f"{self.api_url}/auth/player/rename"
        payload = {
            "nombre_temporal": nombre_temporal,
            "password": password,
            "nuevo_nombre": nuevo_nombre
        }
        try:
            res = requests.post(url, json=payload, timeout=10)
            return res.status_code == 200
        except:
             return False

    def update_birthday(self, birthday: str, token: str):
        """Envía el cumpleaños al servidor (útil para premium o usuarios que omitieron)."""
        url = f"{self.api_url}/player-auth/update-birthday"
        payload = {"birthday": birthday}
        headers = {"Authorization": f"Bearer {token}"}
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            return res.status_code == 200
        except Exception:
            return False

    def get_premium_login_url(self):
        """Genera la URL para el inicio de sesión OAuth de Microsoft."""
        client_id = config.get("microsoft_client_id") or "00000000402B5328"
        # Usamos el redirect estándar para apps de escritorio si es el ID oficial
        redirect_uri = "https://login.live.com/oauth20_desktop.srf"
        
        # Si el usuario configuró uno propio local, se puede usar
        custom_redirect = config.get("microsoft_redirect_uri")
        if custom_redirect:
            redirect_uri = custom_redirect
            
        url = minecraft_launcher_lib.microsoft_account.get_login_url(client_id, redirect_uri)
        return url

    def complete_premium_login(self, code_url_or_code):
        """
        Intercambia el código por un token oficial haciendo el flujo de Xbox/Minecraft manualmente,
        esquivando los bugs internos de minecraft_launcher_lib.
        """
        import urllib.parse
        import requests
        import uuid
        
        client_id = config.get("microsoft_client_id") or "00000000402B5328"
        redirect_uri = "https://login.live.com/oauth20_desktop.srf"
        
        custom_redirect = config.get("microsoft_redirect_uri")
        if custom_redirect:
            redirect_uri = custom_redirect

        # 1. Limpieza de URL
        code = str(code_url_or_code).strip()
        if "code=" in code:
            try:
                parsed = urllib.parse.urlparse(code)
                code = urllib.parse.parse_qs(parsed.query)['code'][0]
            except:
                 pass
        code = urllib.parse.unquote(code).strip()

        try:
            # PASO 1: Obtener Token de Microsoft (La petición que sabemos que funciona)
            ms_req = requests.post("https://login.live.com/oauth20_token.srf", data={
                "client_id": client_id,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            })
            ms_data = ms_req.json()
            if "access_token" not in ms_data:
                return {"status": "ERROR", "message": "Microsoft rechazó el código."}
            
            ms_token = ms_data["access_token"]
            refresh_token = ms_data["refresh_token"]

            # PASO 2: Autenticar en Xbox Live (XBL)
            xbl_req = requests.post("https://user.auth.xboxlive.com/user/authenticate", json={
                "Properties": {
                    "AuthMethod": "RPS",
                    "SiteName": "user.auth.xboxlive.com",
                    "RpsTicket": f"d={ms_token}"
                },
                "RelyingParty": "http://auth.xboxlive.com",
                "TokenType": "JWT"
            })
            xbl_data = xbl_req.json()
            xbl_token = xbl_data["Token"]
            user_hash = xbl_data["DisplayClaims"]["xui"][0]["uhs"]

            # PASO 3: Autenticar en Xbox Secure Token Service (XSTS)
            xsts_req = requests.post("https://xsts.auth.xboxlive.com/xsts/authorize", json={
                "Properties": {
                    "SandboxId": "RETAIL",
                    "UserTokens": [xbl_token]
                },
                "RelyingParty": "rp://api.minecraftservices.com/",
                "TokenType": "JWT"
            })
            xsts_data = xsts_req.json()
            
            # Control de errores comunes de Xbox
            if "err" in xsts_data or "XErr" in xsts_data:
                err_code = xsts_data.get("XErr")
                if err_code == 2148916233: return {"status": "ERROR", "message": "No tienes una cuenta de Xbox creada en este correo."}
                elif err_code == 2148916238: return {"status": "ERROR", "message": "Las cuentas infantiles necesitan ser añadidas a un grupo familiar de Microsoft."}
                return {"status": "ERROR", "message": f"Error de XSTS: {err_code}"}
                
            xsts_token = xsts_data["Token"]

            # PASO 4: Autenticar en los servicios de Minecraft
            mc_req = requests.post("https://api.minecraftservices.com/authentication/login_with_xbox", json={
                "identityToken": f"XBL3.0 x={user_hash};{xsts_token}"
            })
            mc_data = mc_req.json()
            mc_token = mc_data["access_token"]

            # PASO 5: Obtener el perfil real de Minecraft (UUID y Nickname)
            profile_req = requests.get("https://api.minecraftservices.com/minecraft/profile", headers={
                "Authorization": f"Bearer {mc_token}"
            })
            profile_data = profile_req.json()
            
            if "error" in profile_data:
                return {"status": "ERROR", "message": "No tienes el juego comprado en esta cuenta de Microsoft."}

            # Empaquetamos todo exactamente como la librería lo espera para iniciar el juego
            auth_data = {
                "access_token": mc_token,
                "client_token": str(uuid.uuid4()), # Generamos un cliente temporal
                "uuid": profile_data["id"],
                "name": profile_data["name"],
                "user_type": "msa",
                "refresh_token": refresh_token # Clave para que el auto-login funcione mañana
            }

            return {"status": "OK", "data": auth_data}

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"status": "ERROR", "message": f"Error en el flujo manual de autenticación: {str(e)}"}

    def start_integrated_premium_login(self, success_callback, error_callback):
        """
        Ejecuta el login de Microsoft usando el proceso WebView externo de forma desacoplada.
        """
        import subprocess
        import os
        
        client_id = config.get("microsoft_client_id") or "00000000402B5328"
        redirect_uri = "https://login.live.com/oauth20_desktop.srf"
        
        login_url = minecraft_launcher_lib.microsoft_account.get_login_url(client_id, redirect_uri)
        script_path = os.path.join("core", "webview_login.py")
        
        python_exe = os.path.join("venv", "Scripts", "python.exe")
        if not os.path.exists(python_exe):
             python_exe = "python"

        try:
            print(f"[Auth] Iniciando WebView integrado ({script_path})...")
            proceso = subprocess.Popen(
                [python_exe, script_path, login_url, redirect_uri],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0 # Opcional: ocultar consola cmd detrás del WebView
            )
            
            def monitor_stdout():
                # Leer línea por línea
                for linea in proceso.stdout:
                    if linea.startswith("CODE:"):
                        # Extraemos y limpiamos espacios o saltos de línea al instante
                        code = linea.split("CODE:")[1].strip() 
                        print(f"[Auth] ¡Código capturado desde WebView!: {code}")
                        
                        # Pasamos el código limpio
                        success_callback(code) 
                        try: proceso.terminate() 
                        except: pass
                        return
                
                # Si termina sin código, reportar error o cancelación
                rc = proceso.wait()
                if rc != 0:
                     error_callback("El proceso de inicio de sesión fue cancelado o falló.")
                        
            threading.Thread(target=monitor_stdout, daemon=True).start()

        except Exception as e:
            error_callback(f"Error al iniciar WebView: {e}")

    def notify_premium_login_backend(self, username, uuid, access_token="", refresh_token=""):
        """Notifica al backend que un jugador premium ha entrado (crea/actualiza su cuenta)."""
        url = f"{self.api_url}/player-auth/login/premium"
        payload = {
            "username_oficial": username,
            "uuid_oficial": uuid,
            "microsoft_refresh_token": refresh_token,
            "minecraft_access_token": access_token
        }
        try:
            res = requests.post(url, json=payload, timeout=5)
            if res.status_code == 200:
                data = res.json().get("data", {})
                return data.get("access_token", "")
        except:
            pass
        return ""

    def get_player_profile(self, player_token: str) -> dict:
        """Obtiene el perfil completo del jugador autenticado."""
        url = f"{self.api_url}/player-auth/profile"
        try:
            print(f"[Auth] Solicitando perfil a: {url}")
            res = requests.get(url, headers={"Authorization": f"Bearer {player_token}"}, timeout=10)
            print(f"[Auth] Perfil response: {res.status_code}")
            
            if res.status_code == 200:
                data = res.json().get("data", {})
                print(f"[Auth] Perfil cargado: {len(data.get('achievements', []))} logros.")
                return data
            elif res.status_code == 401:
                print(f"[Auth] ERROR: Sesión inválida o expirada (401).")
                return {"_error": "auth_failed"}
            else:
                print(f"[Auth] Error al obtener perfil: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"[Auth] Excepción al obtener perfil: {str(e)}")
        return {}

    def update_player_stats(self, player_token: str, server_name: str, **kwargs) -> bool:
        """Envía estadísticas acumuladas de una sesión al backend."""
        url = f"{self.api_url}/player-auth/stats/update"
        payload = {"server_name": server_name, **kwargs}
        try:
            res = requests.post(url, json=payload,
                                headers={"Authorization": f"Bearer {player_token}"}, timeout=10)
            return res.status_code == 200
        except:
            return False

    def get_leaderboard(self) -> list:
        """Obtiene el top 20 de jugadores."""
        url = f"{self.api_url}/player-auth/leaderboard"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                return res.json().get("data", [])
        except:
            pass
        return []

    def update_skin_no_premium(self, player_token, skin_base64=None, skin_value=None, skin_signature=None):
        """Sincroniza la skin de un jugador No-Premium con el backend."""
        url = f"{self.api_url}/player-auth/update-skin"
        headers = {"Authorization": f"Bearer {player_token}"}
        payload = {}
        if skin_base64: payload["skin_base64"] = skin_base64
        if skin_value: payload["skin_value"] = skin_value
        if skin_signature: payload["skin_signature"] = skin_signature
        
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=15)
            if res.status_code == 200:
                return {"status": "OK", "message": "Skin sincronizada con el servidor."}
            return {"status": "ERROR", "message": f"Error del servidor: {res.status_code}"}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}

    def ensure_valid_session(self) -> str:
        """
        Checks if the current player_token is valid.
        If not, attempts auto-login (No-Premium) or Refresh (Premium).
        Returns a valid token or empty string if it fails.
        """
        token = config.get("player_token")
        if not token:
            return ""

        # 1. Test current token
        profile = self.get_player_profile(token)
        if "_error" not in profile:
            return token

        print("[Auth] Session expired. Attempting auto-login...")

        auth_type = config.get("auth_type")
        acc_type = config.get("account_type")

        # 2. Attempt Auto-Login
        if acc_type == "server" or auth_type == "nopremium":
            username = config.get("username")
            password = config.get("password")
            if username and password:
                print(f"[Auth] Auto-login No-Premium for {username}...")
                res = self.login_no_premium(username, password)
                if res.get("status") == "OK":
                    new_token = res["data"]["token"]
                    config.set("player_token", new_token)
                    return new_token

        elif acc_type == "premium" or auth_type == "premium":
            from core.security import encrypt_data
            from core.oauth import refresh_tokens
            
            ms_refresh_token = config.get("ms_refresh_token")
            if ms_refresh_token:
                print("[Auth] Refreshing Premium session...")
                res = refresh_tokens(ms_refresh_token)
                if res.get("status") == "OK":
                    data = res["data"]
                    # Update MSA token (encrypted in config)
                    config.set("auth_token", encrypt_data(data["access_token"]))
                    
                    # Notify backend to get new LiderAuth token
                    new_player_token = self.notify_premium_login_backend(
                        data["name"], data["uuid"],
                        data["access_token"], data["refresh_token"]
                    )
                    if new_player_token:
                        config.set("player_token", new_player_token)
                        config.set("ms_refresh_token", data["refresh_token"])
                        return new_player_token

        print("[Auth] Auto-login failed.")
        return ""

    def upload_skin(self, skin_path, variant="classic"):
        """Sube la skin a los servidores de Mojang para cuentas Premium."""
        import os
        from core.security import decrypt_data
        
        auth_token = config.get("auth_token")
        if not auth_token:
             return {"status": "ERROR", "message": "No hay token de autenticación."}
             
        access_token = decrypt_data(auth_token)
        url = "https://api.minecraftservices.com/minecraft/profile/skins"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        try:
             if not os.path.exists(skin_path):
                  return {"status": "ERROR", "message": "Archivo de skin no encontrado."}
                  
             with open(skin_path, 'rb') as f:
                  files = {
                      'file': (os.path.basename(skin_path), f, 'image/png')
                  }
                  data = {
                      'variant': variant # 'classic' o 'slim'
                  }
                  respuesta = requests.post(url, headers=headers, files=files, data=data, timeout=10)
                  
                  if respuesta.status_code in [200, 204]:
                       return {"status": "OK", "message": "Skin subida correctamente a Mojang."}
                  else:
                       try: error_msg = respuesta.json().get("errorMessage", "Error desconocido")
                       except: error_msg = f"HTTP {respuesta.status_code}"
                       return {"status": "ERROR", "message": f"Error Mojang: {error_msg}"}
        except Exception as e:
             return {"status": "ERROR", "message": f"Error de conexión: {str(e)}"}

class LocalOAuthListener(http.server.BaseHTTPRequestHandler):
    """Manejador para capturar de forma pasiva la redirección OAuth local."""
    def log_message(self, format, *args): pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        
        if 'code' in query:
             self.server.captured_code = query['code'][0]
             self.send_response(200)
             self.send_header('Content-Type', 'text/html; charset=utf-8')
             self.end_headers()
             self.wfile.write("<h1>Autenticado correctamente.</h1><p>Puedes cerrar esta ventana y volver al launcher.</p>".encode('utf-8'))
        else:
             self.send_error(400, "Falta el código de autorización.")

def start_oauth_listener(port=5000):
    """Prueba de concepto para escuchar automáticamente (requiere configurar redirect_uri en Azure)"""
    class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
         captured_code = None

    server = ThreadedTCPServer(("127.0.0.1", port), LocalOAuthListener)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread
