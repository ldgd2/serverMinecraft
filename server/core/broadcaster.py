from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio

class Broadcaster:
    def __init__(self):
        # server_name -> list of websockets
        self.console_clients: Dict[str, List[WebSocket]] = {}
        # server_name -> list of (websocket, username)
        self.chat_clients: Dict[str, List[Dict]] = {}
        self.status_clients: Dict[str, List[WebSocket]] = {}

    async def connect(self, server_name: str, websocket: WebSocket, client_type: str, username: str = None):
        await websocket.accept()
        if client_type == "console":
            if server_name not in self.console_clients: self.console_clients[server_name] = []
            self.console_clients[server_name].append(websocket)
        elif client_type == "chat":
            if server_name not in self.chat_clients: self.chat_clients[server_name] = []
            self.chat_clients[server_name].append({
                "ws": websocket,
                "username": username
            })
        elif client_type == "status":
            if server_name not in self.status_clients: self.status_clients[server_name] = []
            self.status_clients[server_name].append(websocket)

    def disconnect(self, server_name: str, websocket: WebSocket, client_type: str):
        if client_type == "console":
            clients = self.console_clients.get(server_name, [])
            if websocket in clients: clients.remove(websocket)
        elif client_type == "chat":
            clients = self.chat_clients.get(server_name, [])
            # Find and remove by ws reference
            self.chat_clients[server_name] = [c for c in clients if c["ws"] != websocket]
        elif client_type == "status":
            clients = self.status_clients.get(server_name, [])
            if websocket in clients: clients.remove(websocket)

    async def broadcast_chat(self, server_name: str, sender: str, message: str, is_system: bool = False, **kwargs):
        if server_name in self.chat_clients:
            for client_info in self.chat_clients[server_name]:
                client = client_info["ws"]
                client_user = client_info["username"]
                
                # Determine chat type for THIS specific client
                # If it's a system message, use 'received' or provided type
                # If it's a user message:
                # - If THIS client is the sender, use 'sent'
                # - Otherwise, use 'received'
                
                final_chat_type = kwargs.get("chat_type", "received")
                if not is_system and sender and client_user:
                    if sender == client_user:
                        final_chat_type = "sent"
                    else:
                        final_chat_type = "received"
                
                data = json.dumps({
                    "type": "chat",
                    "sender": sender,
                    "message": message,
                    "is_system": is_system,
                    "chat_type": final_chat_type
                })
                
                try:
                    await client.send_text(data)
                except:
                    pass

    async def broadcast_status(self, server_name: str, stats: dict):
        if server_name in self.status_clients:
            data = json.dumps(stats)
            for client in self.status_clients[server_name]:
                try:
                    await client.send_text(data)
                except:
                    pass

    async def broadcast_console(self, server_name: str, line: str):
        if server_name in self.console_clients:
            for client in self.console_clients[server_name]:
                try:
                    await client.send_text(line)
                except:
                    pass

broadcaster = Broadcaster()
