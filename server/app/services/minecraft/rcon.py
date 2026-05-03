"""
RconService - Servicio para enviar comandos al servidor de Minecraft.

Estrategia de envío (en orden de prioridad):
1. stdin del proceso (si fue iniciado por el manager)
2. mcrcon/python-rcon via TCP (si RCON está habilitado en server.properties)
3. Log de error visible en consola
"""
import asyncio
import os
import socket
import struct
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Protocolo RCON mínimo (sin dependencias externas) ────────────────────────

class _RconClient:
    """
    Cliente RCON ligero que implementa el protocolo de Minecraft
    sin necesitar librerías externas.
    """
    PACKET_TYPE_AUTH = 3
    PACKET_TYPE_COMMAND = 2

    def __init__(self, host: str, port: int, password: str, timeout: float = 3.0):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout

    def _build_packet(self, pkt_id: int, pkt_type: int, payload: str) -> bytes:
        body = (payload + "\x00\x00").encode("utf-8")
        length = 4 + 4 + len(body)
        return struct.pack("<iii", length, pkt_id, pkt_type) + body

    def _read_packet(self, sock: socket.socket):
        raw_len = sock.recv(4)
        if not raw_len or len(raw_len) < 4:
            raise ConnectionError("RCON: No se recibió longitud del paquete")
        length = struct.unpack("<i", raw_len)[0]
        data = b""
        while len(data) < length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                raise ConnectionError("RCON: Conexión cerrada durante lectura")
            data += chunk
        pkt_id, pkt_type = struct.unpack("<ii", data[:8])
        payload = data[8:-2].decode("utf-8", errors="replace")
        return pkt_id, pkt_type, payload

    def send(self, command: str) -> str:
        """Envía un comando vía RCON y devuelve la respuesta. Raise en error."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(self.timeout)
            s.connect((self.host, self.port))

            # Auth
            s.sendall(self._build_packet(1, self.PACKET_TYPE_AUTH, self.password))
            pkt_id, _, _ = self._read_packet(s)
            if pkt_id == -1:
                raise PermissionError("RCON: Contraseña incorrecta")

            # Command
            s.sendall(self._build_packet(2, self.PACKET_TYPE_COMMAND, command))
            _, _, response = self._read_packet(s)
            return response


# ─── Servicio central (singleton) ─────────────────────────────────────────────

class RconService:
    """
    Fachada para enviar comandos al servidor de Minecraft.
    Intenta primero via stdin del proceso, luego via RCON TCP.
    """

    def send_command(self, command: str, server_name: Optional[str] = None) -> bool:
        """
        Envía un comando al servidor. Devuelve True si tuvo éxito.
        
        Args:
            command: El comando sin slash inicial, ej: 'say Hola mundo'
            server_name: Nombre del servidor (usa el primero activo si es None)
        """
        # --- Intento 1: stdin del proceso (preferido) ---
        try:
            from app.services.minecraft import server_service
            # Resolve target process
            if server_name:
                process = server_service.get_process(server_name)
            else:
                # Tomar cualquier proceso que esté ONLINE
                process = None
                for name, proc in server_service.servers.items():
                    if proc._status == "ONLINE":
                        process = proc
                        break

            if process and process.process and process.process.stdin:
                # El proceso tiene stdin abierto — enviar directamente
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(process.write(command))
                except RuntimeError:
                    # Estamos en un thread (BackgroundTasks)
                    asyncio.run(process.write(command))
                return True

        except Exception as e:
            logger.warning(f"[RCON] Fallo con stdin: {e}")

        # --- Intento 2: RCON TCP ---
        try:
            host = os.getenv("RCON_HOST", "127.0.0.1")
            port = int(os.getenv("RCON_PORT", "25575"))
            password = os.getenv("RCON_PASSWORD", "")

            if password:
                client = _RconClient(host, port, password)
                client.send(command)
                logger.info(f"[RCON] Comando enviado vía TCP: {command[:60]}")
                return True
            else:
                logger.warning("[RCON] No hay RCON_PASSWORD configurado. Omitiendo RCON TCP.")
        except Exception as e:
            logger.error(f"[RCON] Fallo TCP: {e}")

        # --- Intento 3: Fallback — escribir en stdin de cualquier proceso vivo ---
        try:
            from app.services.minecraft import server_service
            for name, proc in server_service.servers.items():
                if proc.is_process_alive():
                    if proc.process and proc.process.stdin:
                        try:
                            loop = asyncio.get_running_loop()
                            loop.create_task(proc.write(command))
                        except RuntimeError:
                            asyncio.run(proc.write(command))
                        logger.info(f"[RCON] Usando proceso '{name}' como fallback")
                        return True
        except Exception as e:
            logger.error(f"[RCON] Fallo fallback: {e}")

        logger.error(f"[RCON] No se pudo enviar el comando '{command[:60]}'. Sin stdin ni RCON disponible.")
        return False


# Singleton global
rcon_service = RconService()
