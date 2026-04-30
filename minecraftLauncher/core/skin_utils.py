import base64
import os
from PIL import Image

def get_base64_skin(skin_path):
    """Convierte un archivo de imagen a un string Base64."""
    if not skin_path or not os.path.exists(skin_path):
        return None
    try:
        with open(skin_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"[-] [SkinUtils] Error convirtiendo base64: {e}")
        return None

def extract_minecraft_head(skin_source, size=(64, 64)):
    """Extrae la cabeza (cara + casco) de un skin de Minecraft y la escala."""
    try:
        if isinstance(skin_source, str):
             if not skin_source or not os.path.exists(skin_source):
                  return None
             img = Image.open(skin_source)
        else:
             img = skin_source
    except Exception as e:
        print(f"[-] [SkinUtils] Error cargando imagen: {e}")
        return None
    try:
        # La cara base está en (8, 8, 16, 16)
        face = img.crop((8, 8, 16, 16))
        
        # El casco (segunda capa) está en (40, 8, 48, 16)
        try:
            helmet = img.crop((40, 8, 48, 16))
            # Crear una máscara de transparencia del casco si tiene canal Alpha
            if 'A' in img.getbands():
                face.paste(helmet, (0, 0), helmet)
            else:
                # Si no es RGBA, sólo pegar
                face.paste(helmet, (0, 0))
        except:
            pass # Si no hay casco o falla, se queda con la cara
            
        return face.resize(size, Image.Resampling.NEAREST)
    except Exception as e:
        print(f"[-] [SkinUtils] Error procesando cabeza: {e}")
        return None
