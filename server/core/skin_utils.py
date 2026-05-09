import base64
import json
import requests
from PIL import Image
from io import BytesIO
import os

def extract_skin_url(base64_value: str) -> str:
    """Decodifica el base64 y extrae la URL de la textura de skin."""
    try:
        decoded = base64.b64decode(base64_value).decode('utf-8')
        data = json.loads(decoded)
        return data['textures']['SKIN']['url']
    except Exception:
        return None

def download_and_crop_head(skin_url: str, output_path: str, size: int = 64):
    """Descarga la skin, recorta la cabeza y la guarda escalada."""
    response = requests.get(skin_url)
    skin = Image.open(BytesIO(response.content)).convert('RGBA')
    # Cara base (8,8)-(16,16)
    face = skin.crop((8, 8, 16, 16)).resize((size, size), Image.NEAREST)
    # Casco/sombrero (40,8)-(48,16)
    helmet = skin.crop((40, 8, 48, 16)).resize((size, size), Image.NEAREST)
    # Superponer casco
    final = Image.alpha_composite(face, helmet)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final.save(output_path)
    return output_path

def upload_to_mineskin(base64_png: str) -> dict:
    """
    Sube un PNG base64 a MineSkin para obtener una textura firmada por Mojang.
    Implementa reintentos automáticos para el error 429 (Rate Limit).
    Retorna {'value': '...', 'signature': '...'} o None.
    """
    import time
    
    # 1. Validar dimensiones y detectar modelo (Slim vs Classic)
    try:
        image_data = base64.b64decode(base64_png)
        img = Image.open(BytesIO(image_data))
        width, height = img.size
        print(f"[SkinUtils] Procesando skin de {width}x{height}...")
        
        if (width, height) not in [(64, 32), (64, 64)]:
            print(f"⚠️ Alerta: Dimensiones de skin no estándar ({width}x{height}). MineSkin podría rechazarla.")
        
        # Detección básica de Slim (Alex): Pixeles transparentes en la zona de brazos de 4px
        # En skins de 64x64, el brazo derecho empieza en (40, 16). 
        # Si el pixel en la columna 47 (la 4ta del brazo de 4px) es transparente, suele ser Slim (3px).
        model = "steve"
        if height == 64:
            try:
                # Comprobar transparencia en una zona que solo existe en brazos Classic
                pixel = img.getpixel((47, 20)) # Un punto en el borde del brazo derecho
                if pixel[3] == 0: model = "slim"
            except: pass
        print(f"[SkinUtils] Modelo detectado: {model}")
            
    except Exception as e:
        print(f"[SkinUtils] Error validando imagen: {e}")
        return None

    # 2. Subida con reintentos para 429
    url = "https://api.mineskin.org/generate/upload"
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            files = {'file': ('skin.png', image_data, 'image/png')}
            data = {'visibility': 0, 'model': model}
            
            resp = requests.post(url, files=files, data=data, timeout=30)
            
            if resp.status_code == 200:
                json_data = resp.json()
                texture = json_data.get('data', {}).get('texture', {})
                return {
                    'value': texture.get('value'),
                    'signature': texture.get('signature')
                }
            
            if resp.status_code == 429:
                # MineSkin a veces dice cuánto esperar en el body o cabeceras
                wait_time = 5 # Default 5s
                try:
                    retry_after = resp.headers.get("Retry-After")
                    if retry_after: wait_time = int(retry_after)
                    else:
                        body = resp.json()
                        # El log del usuario dice: "next request in 2618ms"
                        if 'delay' in body: wait_time = (body['delay'] / 1000) + 0.5
                except: pass
                
                print(f"[SkinUtils] MineSkin 429 (Límite). Reintentando en {wait_time}s... (Intento {attempt+1}/{max_retries})")
                time.sleep(wait_time)
                continue
            
            # Error fatal (400, 500, etc.)
            try: err_detail = resp.json().get('error', resp.text)
            except: err_detail = resp.text
            print(f"[SkinUtils] MineSkin Error {resp.status_code}: {err_detail}")
            break
            
        except Exception as e:
            print(f"[SkinUtils] Excepción en subida (intento {attempt+1}): {e}")
            time.sleep(2)
            
    return None
