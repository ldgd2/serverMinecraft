import re
from datetime import datetime
from typing import Dict, Any, Optional

import threading

class PlayerManager:
    def __init__(self):
        # Store players as {username: {ip: str, uuid: str, joined_at: datetime}}
        self.online_players = {}
        self._lock = threading.Lock()

    def add_player(self, username: str, data: Dict[str, Any] = None):
        with self._lock:
            if username not in self.online_players:
                self.online_players[username] = data or {}
            else:
                self.online_players[username].update(data or {})

    def get_player(self, username: str):
        with self._lock:
            return self.online_players.get(username)

    def remove_player(self, username: str):
        with self._lock:
            if username in self.online_players:
                del self.online_players[username]

    def parse_log_line(self, line: str, update_state: bool = True):
        """
        Parse a log line and update player list.
        Returns an event dict if a relevant event occurred, else None.
        Event keys: type, user, reason, timestamp (if found)
        """
        cleaned_line = line.strip()
        timestamp = None
        cleaned_line = line.strip()
        timestamp = None
        
        # Extract timestamp [HH:MM:SS]
        ts_match = re.search(r'^\[(\d{2}:\d{2}:\d{2})\]', cleaned_line)
        if ts_match:
            # We don't have date here, caller might handle date
            timestamp = ts_match.group(1)

        # Pattern 1: UUID (Info only, doesn't change online state but useful)
        # "UUID of player Username is uuid-here"
        if "UUID of player" in cleaned_line:
            match = re.search(r'UUID of player (\S+) is ([a-f0-9-]+)', cleaned_line)
            if match:
                username = match.group(1)
                uuid = match.group(2)
                if update_state:
                    if username not in self.online_players:
                        self.online_players[username] = {}
                    self.online_players[username]['uuid'] = uuid
                return None # No state change yet

        # Pattern 2: Login (Technical - contains IP)
        # "Username[/IP:port] logged in with entity id..."
        # Regex to capture Username, IP
        match_login = re.search(r':\s(\S+)\[/([0-9.]+):\d+\]\slogged\sin', cleaned_line)
        if match_login:
            username = match_login.group(1)
            ip = match_login.group(2)
            
            if update_state:
                with self._lock:
                    if username not in self.online_players:
                        self.online_players[username] = {}
                    
                    self.online_players[username]['ip'] = ip
                    if 'joined_at' not in self.online_players[username]:
                         self.online_players[username]['joined_at'] = datetime.now().isoformat()
            
            return {'type': 'join', 'user': username, 'reason': 'Joined the game', 'timestamp': timestamp}

        # Pattern 3: Join Message (Visible to players)
        # "Username joined the game"
        match_join_msg = re.search(r':\s(\S+)\sjoined\sthe\sgame', cleaned_line)
        if match_join_msg:
            username = match_join_msg.group(1)
            if update_state:
                with self._lock:
                    if username not in self.online_players:
                        self.online_players[username] = {'joined_at': datetime.now().isoformat()}
            return {'type': 'join', 'user': username, 'reason': 'Joined the game', 'timestamp': timestamp}

        # Pattern 4: Lost Connection (Generic disconnect/timeout/kick)
        # "Username lost connection: Reason"
        match_lost = re.search(r':\s(\S+)\slost\sconnection:\s(.*)', cleaned_line)
        if match_lost:
            username = match_lost.group(1)
            reason = match_lost.group(2)
            if update_state:
                with self._lock:
                    if username in self.online_players:
                        del self.online_players[username]
                
            # Refine reason for event log
            event_type = 'leave'
            if "Kicked" in reason or "kicked" in reason:
                event_type = 'kick'
            elif "Timed out" in reason:
                event_type = 'leave' # or timeout
                
            return {'type': event_type, 'user': username, 'reason': reason, 'timestamp': timestamp}

        # Pattern 5: Left the game (Voluntary or consequence of lost connection)
        # "Username left the game"
        match_left = re.search(r':\s(\S+)\sleft\sthe\sgame', cleaned_line)
        if match_left:
            username = match_left.group(1)
            if update_state:
                with self._lock:
                    if username in self.online_players:
                        del self.online_players[username]
                    return {'type': 'leave', 'user': username, 'reason': 'Left the game', 'timestamp': timestamp}
            else:
                 return {'type': 'leave', 'user': username, 'reason': 'Left the game', 'timestamp': timestamp}
            
            # If not in list (already processed lost connection), we don't return event if scanning history?
            # Actually logic in original file was: if update_state=false, return event.
            # If update_state=true and not in list (already processed via lost connection), return None to avoid duplicate Notification?
            # But duplicate check logic happens upstairs in _add_activity.
            return None

        # Pattern 6: Console Kicks/Bans (Explicit)
        if "Kicked " in cleaned_line and " lost connection" not in cleaned_line:
             match_kick = re.search(r'Kicked ([a-zA-Z0-9_]+): (.*)', cleaned_line)
             if match_kick:
                 return {'type': 'kick', 'user': match_kick.group(1), 'reason': match_kick.group(2), 'timestamp': timestamp}

        if "Banned " in cleaned_line and " IP " not in cleaned_line:
            match_ban = re.search(r'Banned ([a-zA-Z0-9_]+): (.*)', cleaned_line)
            if match_ban:
                return {'type': 'ban', 'user': match_ban.group(1), 'reason': match_ban.group(2), 'timestamp': timestamp}
        
        if "Banned IP " in cleaned_line:
             match_banip = re.search(r'Banned IP ([0-9.]+): (.*)', cleaned_line)
             if match_banip:
                 return {'type': 'ban-ip', 'user': match_banip.group(1), 'reason': match_banip.group(2), 'timestamp': timestamp}

        if "Unbanned " in cleaned_line and " IP " not in cleaned_line:
             match_unban = re.search(r'Unbanned ([a-zA-Z0-9_]+)', cleaned_line)
             if match_unban:
                  return {'type': 'unban', 'user': match_unban.group(1), 'reason': 'Unbanned', 'timestamp': timestamp}

        if "Unbanned IP " in cleaned_line:
             match_unbanip = re.search(r'Unbanned IP ([0-9.]+)', cleaned_line)
             if match_unbanip:
                  return {'type': 'unban-ip', 'user': match_unbanip.group(1), 'reason': 'Unbanned IP', 'timestamp': timestamp}
                  
        return None

    def get_players(self):
        with self._lock:
            return [
                {"username": u, **d.copy()} 
                for u, d in self.online_players.items()
            ]
    
    def get_count(self):
        with self._lock:
            return len(self.online_players)
