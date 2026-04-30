"""
core/oauth.py
Clean Microsoft OAuth2 flow using a local HTTP server callback.

Flow:
1. Build the Azure authorization URL
2. Open it in the user's default browser
3. Listen on http://localhost:3000/callback for the redirect
4. Extract the `code` from the query string
5. Exchange it for tokens via minecraft_launcher_lib
"""
import os
import threading
import webbrowser
import http.server
import urllib.parse
import requests
from typing import Callable, Optional


# ── Load from .env ─────────────────────────────────────────────────────────────

def _load_env():
    """Read key=value pairs from .env in the project root."""
    env = {}
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root, ".env")
    if not os.path.exists(env_path):
        return env
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


_ENV = _load_env()

# Client ID: .env > os.environ > fallback
CLIENT_ID     = _ENV.get("AZURE_CLIENT_ID") or os.environ.get("AZURE_CLIENT_ID") or "null"
REDIRECT_URI  = _ENV.get("AZURE_REDIRECT_URI") or os.environ.get("AZURE_REDIRECT_URI") or "http://localhost:3000/callback"
import subprocess

# ── Public API ─────────────────────────────────────────────────────────────────

def build_auth_url() -> str:
    """Build the Microsoft OAuth authorization URL using the Azure Client ID."""
    import minecraft_launcher_lib
    url = minecraft_launcher_lib.microsoft_account.get_login_url(CLIENT_ID, REDIRECT_URI)
    return url


def start_oauth_flow(
    on_success: Callable[[str], None],
    on_error:   Callable[[str], None],
) -> None:
    """
    1. Build the auth URL
    2. Start the pywebview process (webview_login.py)
    3. Read the code from its stdout
    4. Call on_success(code) or on_error(message)
    """
    auth_url = build_auth_url()
    print(f"[OAuth] Opening WebView: {auth_url}")

    def _run():
        import sys
        script_path = os.path.join(os.path.dirname(__file__), "webview_login.py")
        
        if not os.path.exists(script_path):
            on_error("Falta el archivo webview_login.py.")
            return

        # Hide terminal window on Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            proc = subprocess.Popen(
                [sys.executable, script_path, auth_url, REDIRECT_URI],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                # Create a new process group so it doesn't tether strictly 
                # (although startupinfo handles the console mostly)
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            code = None
            for line in proc.stdout:
                line = line.strip()
                if line.startswith("CODE:"):
                    code = line.replace("CODE:", "")
                    break

            proc.stderr.read()  # exhaust stderr just in case
            proc.wait()

            if code:
                on_success(code)
            else:
                on_error("Inicio de sesión cancelado o la ventana se cerró.")

        except Exception as e:
            on_error(f"Error al abrir la ventana de MS: {e}")

    threading.Thread(target=_run, daemon=True).start()


def exchange_code_for_tokens(code: str) -> dict:
    """
    Exchange the OAuth authorization code for Minecraft credentials manually.
    """
    try:
        # 1. Exchange code for MS access token
        r1 = requests.post("https://login.live.com/oauth20_token.srf", data={
            "client_id": CLIENT_ID,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "scope": "XboxLive.signin offline_access"
        })
        if r1.status_code != 200:
            return {"status": "ERROR", "message": f"Exchange code falló: {r1.text}"}
        
        ms_data = r1.json()
        ms_access_token = ms_data["access_token"]
        ms_refresh_token = ms_data.get("refresh_token", "")

        # 2. Xbox Live Auth
        r2 = requests.post("https://user.auth.xboxlive.com/user/authenticate", 
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json={
                "Properties": {
                    "AuthMethod": "RPS",
                    "SiteName": "user.auth.xboxlive.com",
                    "RpsTicket": f"d={ms_access_token}"
                },
                "RelyingParty": "http://auth.xboxlive.com",
                "TokenType": "JWT"
            }
        )
        if r2.status_code != 200:
            return {"status": "ERROR", "message": f"Xbox Live auth falló: {r2.text}"}
            
        xbl_data = r2.json()
        xbl_token = xbl_data["Token"]
        uhs = xbl_data["DisplayClaims"]["xui"][0]["uhs"]

        # 3. XSTS Token
        r3 = requests.post("https://xsts.auth.xboxlive.com/xsts/authorize",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json={
                "Properties": {
                    "SandboxId": "RETAIL",
                    "UserTokens": [xbl_token]
                },
                "RelyingParty": "rp://api.minecraftservices.com/",
                "TokenType": "JWT"
            }
        )
        if r3.status_code != 200:
            return {"status": "ERROR", "message": f"XSTS auth falló: {r3.text}"}
            
        xsts_token = r3.json()["Token"]

        # 4. Minecraft Token
        r4 = requests.post("https://api.minecraftservices.com/authentication/login_with_xbox",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            json={
                "identityToken": f"XBL3.0 x={uhs};{xsts_token}"
            }
        )
        if r4.status_code != 200:
            return {"status": "ERROR", "message": f"Login de Minecraft falló: {r4.text}"}
            
        mc_access_token = r4.json()["access_token"]

        # 5. Minecraft Profile
        r5 = requests.get("https://api.minecraftservices.com/minecraft/profile",
            headers={"Authorization": f"Bearer {mc_access_token}"}
        )
        if r5.status_code != 200:
            return {"status": "ERROR", "message": f"Obtener perfil falló: {r5.text}"}
            
        profile_data = r5.json()

        return {
            "status": "OK",
            "data": {
                "name":          profile_data["name"],
                "uuid":          profile_data["id"],
                "access_token":  mc_access_token,
                "refresh_token": ms_refresh_token,
            }
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}
