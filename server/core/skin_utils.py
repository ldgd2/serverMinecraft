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
