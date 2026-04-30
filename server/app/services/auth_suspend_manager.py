import uuid
import base64
import time
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from typing import Dict, Optional

class AuthChallengeManager:
    def __init__(self):
        # { challenge_id: { "private_key": rsa_key, "public_key": str, "ip": str, "timestamp": float } }
        self.challenges: Dict[str, dict] = {}
        self.ttl = 60.0  # Tiempo de vida del desafío (60 segundos)

    def create_challenge(self, ip: str) -> dict:
        """
        Genera un par de claves RSA y registra un desafío para la IP.
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        public_key = private_key.public_key()
        
        # Serializar clave pública a PEM
        pub_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        challenge_id = str(uuid.uuid4())
        
        self.challenges[challenge_id] = {
            "private_key": private_key,
            "public_key": pub_pem,
            "ip": ip,
            "timestamp": time.time()
        }
        
        # Limpieza periódica (simple) cada vez que se crea uno
        self._cleanup_expired()
        
        return {
            "challenge_id": challenge_id,
            "pub_key": pub_pem
        }

    def validate_challenge(self, challenge_id: str, ip: str) -> bool:
        """
        Verifica si el desafío existe, no ha expirado y pertenece a la IP.
        """
        if challenge_id not in self.challenges:
            return False
            
        data = self.challenges[challenge_id]
        if time.time() - data["timestamp"] > self.ttl:
            del self.challenges[challenge_id]
            return False
            
        if data["ip"] != ip:
            return False
            
        return True

    def decrypt_password(self, challenge_id: str, encrypted_b64: str) -> str:
        """
        Descifra la contraseña usando la clave privada asociada al desafío.
        """
        if challenge_id not in self.challenges:
            raise ValueError("Desadío inválido o expirado")
            
        private_key = self.challenges[challenge_id]["private_key"]
        encrypted_data = base64.b64decode(encrypted_b64)
        
        try:
            decrypted = private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            # Limpiar el desafío una vez usado (por seguridad)
            del self.challenges[challenge_id]
            return decrypted.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Error al descifrar: {str(e)}")

    def _cleanup_expired(self):
        """
        Elimina de memoria los desafíos expirados.
        """
        now = time.time()
        expired = [cid for cid, data in self.challenges.items() if now - data["timestamp"] > self.ttl]
        for cid in expired:
            del self.challenges[cid]

# Instancia Singleton
challenge_manager = AuthChallengeManager()
