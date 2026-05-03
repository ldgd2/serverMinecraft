import time
import threading
import os
import requests
import platform
from config.manager import config
from core.skin_utils import get_base64_skin

def get_player_info():
    """Obtiene IP y país del jugador mediante un servicio externo."""
    try:
        # Intenta obtener IP y país
        res = requests.get('https://ipapi.co/json/', timeout=3)
        if res.status_code == 200:
            data = res.json()
            # Si contiene un error de rate-limit u otro, data no tendrá ip
            if "ip" in data:
                return data.get("ip"), data.get("country_code")
    except:
        pass
    
    # Fallback solo IP si el anterior falla o se bloquea
    try:
        res = requests.get('https://api.ipify.org', timeout=3)
        if res.status_code == 200:
            return res.text.strip(), None
    except:
        pass
    
    return "127.0.0.1", "?? prototype"

def notify_backend(ip_objetivo, username, uuid, url_api):
    """Envía la información del jugador y su skin al backend."""
    try:
        player_ip, player_country = get_player_info()
        payload = {
            "player": username,
            "uuid": uuid if uuid else "",
            "server_id": config.get("server_id") or 1,
            "ip": player_ip,
            "country": player_country if player_country else "??",
            "os": platform.system(),
            "skin_base64": get_base64_skin(config.get("skin_path")) or "",
            "type": "player_state" # Importante para que el bridge lo reconozca
        }
        
        # Obtenemos la API Key desde la configuración para autorizar la petición
        headers = {
            "x-api-key": config.get("api_key") or ""
        }
        
        print(f"[*] [SkinSync] Enviando skin de {username} a {url_api}...")
        response = requests.post(url_api, json=payload, headers=headers, timeout=5)
        print(f"[+] [SkinSync] API respondio: {response.status_code}")
        return True
    except Exception as e:
        print(f"[-] [SkinSync] Error notificando API: {e}")
        return False

def cazador_de_ips(ruta_log, ip_objetivo, username, uuid, url_api):
    """
    Monitorea el log en tiempo real. 
    """
    print(f"[SkinSync] Iniciando monitoreo de log para IP: {ip_objetivo}")
    
    # Intento inicial proactivo
    notify_backend(ip_objetivo, username, uuid, url_api)

    while not os.path.exists(ruta_log): 
        time.sleep(1)
        
    try:
        with open(ruta_log, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(0, 2) 
            
            while True:
                linea = f.readline()
                if not linea:
                    time.sleep(1) 
                    continue
                
                # Patrones comunes de conexión en varias versiones
                if ip_objetivo in linea and ("Connecting to" in linea or "Connecting" in linea):
                    print(f"[*] [SkinSync] Evento de conexión detectado en log. Re-sincronizando...")
                    notify_backend(ip_objetivo, username, uuid, url_api)
                    time.sleep(30) # Cooldown largo para evitar spam
    except Exception as e:
        print(f"[-] [SkinSync] Error en el monitor de log: {e}")

def start_skin_sync_monitor(f_log, ip, username, uuid, api_url):
    hilo = threading.Thread(
        target=cazador_de_ips,
        args=(f_log, ip, username, uuid, api_url),
        daemon=True
    )
    hilo.start()
    return hilo
