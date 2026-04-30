import http.server
import socketserver
import json
import base64
import os
import threading
import time
import uuid
import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

from config.manager import config

# Generate RSA keypair for Yggdrasil signing
print("[SkinServer] Generating RSA keypair for Yggdrasil signing...")
PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PUBLIC_KEY = PRIVATE_KEY.public_key()

PEM_PUBLIC_KEY = PUBLIC_KEY.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode('utf-8')

class SkinHTTPHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence standard HTTP logging to keep console clean
        pass

    def do_GET(self):
        # Remove query parameters for routing
        path = self.path.split('?')[0]
        
        if path == "/":
            self.handle_metadata()
        elif path.startswith("/sessionserver/session/minecraft/profile/"):
            # Extract UUID from path
            parts = path.split('/')
            player_uuid = parts[-1] if parts else ""
            self.handle_profile(player_uuid)
        elif path.startswith("/api/profiles/minecraft"):
            self.handle_api_profiles()
        elif path.startswith("/skin/"):
            self.handle_skin_file()
        else:
            self.send_error(404, "Not Found")

    def handle_metadata(self):
        metadata = {
            "meta": {
                "serverName": "Local Skin Server",
                "implementationName": "Custom Launcher",
                "implementationVersion": "1.0"
            },
            "skinDomains": ["localhost", "127.0.0.1"],
            "signaturePublickey": PEM_PUBLIC_KEY
        }
        self.send_json_response(metadata)

    def handle_profile(self, player_uuid):
        username = config.get("username") or "Player"
        
        # Clean UUID (remove dashes if present)
        clean_uuid = player_uuid.replace('-', '')
        if not clean_uuid:
            # Generate deterministic offline UUID if empty
            m = hashlib.md5()
            m.update(f"OfflinePlayer:{username}".encode('utf-8'))
            clean_uuid = m.hexdigest()

        # 1. Create Texture URL pointing back to this server
        # We don't know our own bound port from here easily, but we can read it from the Host header
        host = self.headers.get('Host', 'localhost:8000')
        skin_url = f"http://{host}/skin/{username}.png"

        # 2. Build Textures JSON
        textures_data = {
            "timestamp": int(time.time() * 1000),
            "profileId": clean_uuid,
            "profileName": username,
            "textures": {
                "SKIN": {
                    "url": skin_url
                }
            }
        }
        
        textures_json = json.dumps(textures_data, separators=(',', ':'))
        textures_base64 = base64.b64encode(textures_json.encode('utf-8')).decode('utf-8')

        # 3. Sign the textures string using SHA1withRSA
        signature = PRIVATE_KEY.sign(
            textures_base64.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA1()
        )
        signature_base64 = base64.b64encode(signature).decode('utf-8')

        # 4. Build Profile Response
        profile = {
            "id": clean_uuid,
            "name": username,
            "properties": [
                {
                    "name": "textures",
                    "value": textures_base64,
                    "signature": signature_base64
                }
            ]
        }
        self.send_json_response(profile)

    def handle_api_profiles(self):
        # Just return the single profile for any requested name to simplify API lookup
        # API expects array or maps, but usually for local skin server we just return empty or single
        self.send_json_response([])

    def handle_skin_file(self):
        skin_path = config.get("skin_path")
        if skin_path and os.path.exists(skin_path):
            try:
                with open(skin_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.send_header('Content-length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            except Exception as e:
                print(f"[-] [SkinServer] Error serving skin file: {e}")
        
        # Fallback to 404 if no skin configured
        self.send_error(404, "Skin Not Configured")

    def send_json_response(self, data):
        content = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

class LocalSkinServer(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.server = None
        self.port = 0

    def run(self):
        # Bind to port 0 to let OS pick an available port
        with socketserver.TCPServer(("127.0.0.1", 0), SkinHTTPHandler) as httpd:
            self.server = httpd
            self.port = httpd.server_address[1]
            print(f"[SkinServer] Local server running at http://127.0.0.1:{self.port}")
            httpd.serve_forever()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("[SkinServer] Local server stopped.")

def start_local_skin_server():
    server = LocalSkinServer()
    server.start()
    # Give it a tiny moment to bind and get port
    while server.port == 0:
         time.sleep(0.05)
    return server
