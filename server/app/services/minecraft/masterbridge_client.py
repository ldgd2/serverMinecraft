"""
MasterBridge API Client
Connects to MasterBridge Fabric mod API for enhanced server monitoring
"""
import requests
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class MasterBridgeClient:
    """Client to interact with MasterBridge Fabric mod API"""
    
    def __init__(self, ip: str = "127.0.0.1", port: int = 8081):
        """
        Initialize MasterBridge client
        
        Args:
            ip: IP address where MasterBridge mod is running
            port: Port where MasterBridge mod is listening
        """
        self.base_url = f"http://{ip}:{port}"
        self.timeout = 5  # seconds
        
    def _make_request(self, endpoint: str, method: str = "GET", data: Dict = None) -> Optional[Dict]:
        """
        Make HTTP request to MasterBridge API
        
        Args:
            endpoint: API endpoint (e.g., '/api/players')
            method: HTTP method
            data: Request payload for POST requests
            
        Returns:
            Response JSON or None if failed
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, timeout=self.timeout)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=self.timeout)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.warning(f"MasterBridge request to {url} timed out")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"Could not connect to MasterBridge at {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"MasterBridge request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in MasterBridge request: {e}")
            return None
    
    def get_full_state(self) -> Optional[Dict]:
        """
        Get full server state
        
        Returns:
            Dict with: online_count, max_players, motd, version, mspt, players_names
        """
        return self._make_request("/api/full-state")
    
    def get_players(self) -> Optional[List[Dict]]:
        """
        Get list of online players from full-state endpoint
        
        Returns:
            List of dicts with player names: [{"name": "player1"}, {"name": "player2"}]
        """
        state = self.get_full_state()
        if state and 'players' in state:
            # Convert list of names to list of dicts with name field
            players = state.get('players', [])
            return [{'name': name} for name in players] if isinstance(players, list) else []
        return None
    
    def get_chat(self) -> Optional[List[Dict]]:
        """
        Get chat messages - MasterBridge mod doesn't have a chat history endpoint
        Chat messages are sent via POST /api/send only
        
        Returns:
            Empty list (no chat history available from mod)
        """
        # MasterBridge mod does not expose chat history
        return []
    
    def send_chat_message(self, text: str) -> bool:
        """
        Send a chat message to the game
        
        Args:
            text: Message text to send
            
        Returns:
            True if successful, False otherwise
        """
        data = {"text": text}
        result = self._make_request("/api/send", method="POST", data=data)
        return result is not None and result.get("status") == "ok"
    
    def is_available(self) -> bool:
        """
        Check if MasterBridge API is available
        
        Returns:
            True if API responds, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/full-state", timeout=2)
            return response.status_code == 200
        except:
            return False

    # --- Moderation ---
    def kick_player(self, name: str, reason: str = "Kicked by operator") -> bool:
        """Kick a player via MasterBridge"""
        data = {"name": name, "reason": reason}
        result = self._make_request("/api/kick", method="POST", data=data)
        return result is not None and result.get("status") == "ok"

    def ban_player(self, name: str, reason: str = "Banned by admin") -> bool:
        """Ban a player via MasterBridge"""
        data = {"name": name, "reason": reason}
        result = self._make_request("/api/ban", method="POST", data=data)
        return result is not None and result.get("status") == "ok"

    def unban_player(self, name: str) -> bool:
        """Unban a player via MasterBridge"""
        data = {"name": name}
        result = self._make_request("/api/unban", method="POST", data=data)
        return result is not None and result.get("status") == "ok"

    # --- Events & Gameplay ---
    def trigger_event(self, context_data: Dict) -> bool:
        """Trigger a generic chaos event"""
        # The Java code accepts a ctx and passes it to ChaosController.handleEvent
        # We assume it accepts a JSON body
        result = self._make_request("/api/events", method="POST", data=context_data)
        return result is not None

    def trigger_cinematic(self, type_name: str, target: str, difficulty: int = 1) -> bool:
        """Trigger a cinematic event"""
        data = {
            "type": type_name,
            "target": target,
            "difficulty": difficulty
        }
        result = self._make_request("/api/cinematics", method="POST", data=data)
        return result is not None and "activada" in str(result.get("status", ""))

    def trigger_paranoia(self, target: str, duration: int = 60) -> bool:
        """Trigger a paranoia event"""
        data = {
            "target": target,
            "duration": duration
        }
        result = self._make_request("/api/paranoia", method="POST", data=data)
        return result is not None and "activada" in str(result.get("status", ""))

    def trigger_special_event(self, event_type: str, target: str) -> bool:
        """Trigger a special event (e.g. admin_coliseum)"""
        data = {
            "type": event_type,
            "target": target
        }
        result = self._make_request("/api/special-events", method="POST", data=data)
        return result is not None and "activada" in str(result.get("status", ""))

    # --- Additional Endpoints ---
    def get_chat_log(self) -> Optional[List[Dict]]:
        """Get complete chat history from MasterBridge"""
        return self._make_request("/api/chat-log")

    def get_online_players_detailed(self) -> Optional[List[Dict]]:
        """
        Get detailed information about online players
        
        Returns:
            List of dicts with: name, uuid, ping, health, food, level, dimension, pos
        """
        return self._make_request("/api/online-players")

    def get_server_status(self) -> Optional[Dict]:
        """
        Get detailed server status
        
        Returns:
            Dict with: online_players, max_players, motd, version, mspt
        """
        return self._make_request("/api/server-status")

    def get_active_events(self) -> Optional[Dict]:
        """
        Get all currently active events
        
        Returns:
            Dict with: wave_events, cinematics, special_event_active
        """
        return self._make_request("/api/active-events")

    def download_resource_pack(self) -> Optional[bytes]:
        """Download server resource pack as ZIP"""
        url = f"{self.base_url}/pack.zip"
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Failed to download resource pack: {e}")
            return None
