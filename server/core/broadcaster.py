from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio
import time

class Broadcaster:
    def __init__(self):
        # server_name -> list of websockets
        self.console_clients: Dict[str, List[WebSocket]] = {}
        # server_name -> list of (websocket, username)
        self.chat_clients: Dict[str, List[Dict]] = {}
        self.status_clients: Dict[str, List[WebSocket]] = {}
        self.last_messages: Dict[str, dict] = {} # For deduplication

    async def connect(self, server_name: str, websocket: WebSocket, client_type: str, username: str = None):
        server_name = server_name.lower()
        await websocket.accept()
        
        if client_type == "console":
            if server_name not in self.console_clients: self.console_clients[server_name] = []
            if websocket not in self.console_clients[server_name]:
                self.console_clients[server_name].append(websocket)
                print(f"[BROADCASTER] {client_type} client joined room: {server_name}")
        elif client_type == "chat":
            if server_name not in self.chat_clients: self.chat_clients[server_name] = []
            # Evitar duplicados (mismo socket)
            if not any(c["ws"] == websocket for c in self.chat_clients[server_name]):
                self.chat_clients[server_name].append({
                    "ws": websocket,
                    "username": username
                })
                print(f"[BROADCASTER] {client_type} client '{username}' joined room: {server_name}")
        elif client_type == "status":
            if server_name not in self.status_clients: self.status_clients[server_name] = []
            if websocket not in self.status_clients[server_name]:
                self.status_clients[server_name].append(websocket)
                print(f"[BROADCASTER] {client_type} client joined room: {server_name}")

    def disconnect(self, server_name: str, websocket: WebSocket, client_type: str):
        server_name = server_name.lower()
        if client_type == "console":
            clients = self.console_clients.get(server_name, [])
            if websocket in clients: clients.remove(websocket)
            print(f"[BROADCASTER] {client_type} client left room: {server_name}")
        elif client_type == "chat":
            clients = self.chat_clients.get(server_name, [])
            self.chat_clients[server_name] = [c for c in clients if c["ws"] != websocket]
            print(f"[BROADCASTER] {client_type} client left room: {server_name}")
        elif client_type == "status":
            clients = self.status_clients.get(server_name, [])
            if websocket in clients: clients.remove(websocket)
            print(f"[BROADCASTER] {client_type} client left room: {server_name}")

    async def broadcast_chat(self, server_name: str, sender: str, message: str, is_system: bool = False, **kwargs):
        server_name = server_name.lower()
        
        # Deduplicación: Si es el mismo mensaje en < 1 segundo, ignorar
        msg_key = f"{server_name}:{sender}:{message}"
        now = time.time()
        if msg_key in self.last_messages:
            last_time = self.last_messages[msg_key]
            if now - last_time < 1.0:
                print(f"DEBUG: Broadcaster: Ignoring duplicate message: {msg_key}")
                return
        self.last_messages[msg_key] = now
        
        # Limpiar caché de mensajes antiguos cada cierto tiempo (opcional, pero buena práctica)
        if len(self.last_messages) > 100:
            self.last_messages = {k: v for k, v in self.last_messages.items() if now - v < 5.0}

        clients = self.chat_clients.get(server_name, [])
        if not clients:
            return

        print(f"DEBUG: Broadcaster: Broadcasting to {len(clients)} clients in {server_name}: <{sender}> {message[:30]}...")
        for client_info in list(clients):
            client = client_info["ws"]
            client_user = client_info["username"]
            
            # Determinar el tipo de chat (sent/received)
            final_chat_type = kwargs.get("chat_type", "received")
            if not is_system and sender:
                # Si el que envía es el mismo que está conectado, marcar como 'sent'
                if client_user and sender.lower() == client_user.lower():
                    final_chat_type = "sent"
                else:
                    final_chat_type = "received"
            
            # Incluir URL de la cabeza para la App
            head_url = kwargs.get("head_url")
            if not head_url and not is_system and sender:
                head_url = f"/static/heads/{sender}.png"

            data = json.dumps({
                "type": "chat",
                "sender": sender,
                "message": message,
                "is_system": is_system,
                "chat_type": final_chat_type,
                "head_url": head_url
            })
            
            try:
                await client.send_text(data)
                print(f"DEBUG: Broadcaster: Sent chat to {client_user} in {server_name}")
            except Exception as e:
                print(f"DEBUG: Broadcaster: Chat send error to {client_user}: {e}")
                try: self.chat_clients[server_name].remove(client_info)
                except: pass

    async def broadcast_status(self, server_name: str, stats: dict):
        server_name = server_name.lower()
        clients = self.status_clients.get(server_name, [])
        if not clients:
            return

        data = json.dumps(stats)
        for client in list(clients):
            try:
                await client.send_text(data)
            except Exception as e:
                print(f"DEBUG: Broadcaster: Status send error: {e}")
                try: self.status_clients[server_name].remove(client)
                except: pass

    async def broadcast_console(self, server_name: str, line: str):
        server_name = server_name.lower()
        if server_name in self.console_clients:
            for client in list(self.console_clients[server_name]):
                try:
                    await client.send_text(line)
                except Exception as e:
                    print(f"DEBUG: Broadcaster: Console send error: {e}")
                    try: self.console_clients[server_name].remove(client)
                    except: pass

broadcaster = Broadcaster()
