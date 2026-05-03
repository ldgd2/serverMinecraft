from sqlalchemy.orm import Session
from database.models import Server
from database.models.players.player import Player
from database.models.players.player_ban import PlayerBan
from database.models.players.player_detail import PlayerDetail
from app.services.minecraft import server_service
from app.services.bitacora_service import BitacoraService
import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

class BanDurationType(str, Enum):
    """Enum for ban duration types"""
    PERMANENT = "permanent"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"

class PlayerService:
    """Service for managing player bans, kicks, and related operations"""

    @staticmethod
    def get_online_players(server_name: str) -> List[Dict[str, Any]]:
        """
        Get list of currently online players on a server.
        Prioriza la caché en memoria del Bridge (actualizada por push del Mod),
        evitando lecturas de disco costosas. Solo hace fallback a log parsing si la caché está vacía.
        """
        # 1. Intentar con la caché del Bridge (fuente de verdad más eficiente)
        try:
            from routes.bridge import server_player_cache
            cached = server_player_cache.get(server_name)
            if cached is not None:  # La caché existe (aunque esté vacía => servidor recién iniciado)
                return [
                    {"username": name, **data}
                    for name, data in cached.items()
                ]
        except Exception:
            pass

        # 2. Fallback: log parsing via PlayerManager (sólo si el Bridge no tiene datos)
        process = server_service.get_process(server_name)
        if not process:
            return []
        return process.player_manager.get_players()

    @staticmethod
    def get_player_by_uuid(db: Session, server: Server, uuid: str) -> Optional[Player]:
        """Get player from database by UUID"""
        player = db.query(Player).filter(
            Player.server_id == server.id,
            Player.uuid == uuid
        ).first()
        return player

    @staticmethod
    def get_player_by_name(db: Session, server: Server, name: str) -> Optional[Player]:
        """Get player from database by name (case-insensitive)"""
        player = db.query(Player).filter(
            Player.server_id == server.id,
            Player.name.ilike(name)  # Case-insensitive search
        ).first()
        return player

    @staticmethod
    def calculate_ban_expiry(duration_type: str, duration_value: int) -> Optional[datetime.datetime]:
        """
        Calculate ban expiry datetime based on duration type and value.
        Returns None for permanent bans.
        """
        if duration_type == BanDurationType.PERMANENT or duration_type == "permanent":
            return None
        
        now = datetime.datetime.utcnow()
        
        if duration_type == BanDurationType.HOURS or duration_type == "hours":
            return now + datetime.timedelta(hours=duration_value)
        elif duration_type == BanDurationType.DAYS or duration_type == "days":
            return now + datetime.timedelta(days=duration_value)
        elif duration_type == BanDurationType.WEEKS or duration_type == "weeks":
            return now + datetime.timedelta(weeks=duration_value)
        elif duration_type == BanDurationType.MONTHS or duration_type == "months":
            # Approximate: 1 month = 30 days
            return now + datetime.timedelta(days=duration_value * 30)
        
        return None

    @staticmethod
    async def ban_player(
        db: Session,
        server: Server,
        player_identifier: str,  # UUID or username
        reason: str,
        duration_type: str = "permanent",
        duration_value: int = 0,
        issued_by: str = "Console"
    ) -> Dict[str, Any]:
        """
        Ban a player (temporary or permanent)
        
        Args:
            db: Database session
            server: Server instance
            player_identifier: UUID or player name
            reason: Ban reason
            duration_type: "permanent", "hours", "days", "weeks", "months"
            duration_value: Number of units for duration_type
            issued_by: User/admin who issued the ban
            
        Returns:
            Dict with ban information and success status
        """
        
        # Find player in database
        player = PlayerService.get_player_by_uuid(db, server, player_identifier)
        if not player:
            player = PlayerService.get_player_by_name(db, server, player_identifier)
        
        if not player:
            return {
                "success": False,
                "message": f"Player '{player_identifier}' not found in server '{server.name}'",
                "error": "PLAYER_NOT_FOUND"
            }
        
        # Calculate expiry
        expires_at = PlayerService.calculate_ban_expiry(duration_type, duration_value)
        
        # Create ban record
        ban = PlayerBan(
            player_uuid=player.uuid,
            server_id=server.id,
            is_active=True,
            reason=reason,
            source=issued_by,
            issued_at=datetime.datetime.utcnow(),
            expires_at=expires_at
        )
        
        db.add(ban)
        
        # Execute ban command on server (if online)
        process = server_service.get_process(server.name)
        if process and process.is_running():
            await process.write(f"ban {player.name} {reason}")
            
        # Also notify via Bridge if connected
        from routes.bridge import manager as bridge_manager
        # Assuming server username matches some identifier, but usually it's the server owner's username
        # For now, we search for the server owner's connection
        from database.models.user import User
        owner = db.query(User).filter(User.id == server.user_id).first()
        if owner:
            await bridge_manager.send_ban(owner.username, player.name, reason)
        
        db.commit()
        
        # Audit log
        ban_duration = (
            "permanent" if expires_at is None 
            else f"{duration_value} {duration_type}"
        )
        BitacoraService.add_log(
            db, 
            issued_by, 
            "PLAYER_BAN", 
            f"Banned player {player.name} ({player.uuid}) for {ban_duration}: {reason}"
        )
        
        return {
            "success": True,
            "message": f"Player '{player.name}' has been banned",
            "player": {
                "uuid": player.uuid,
                "name": player.name,
                "ban": {
                    "reason": reason,
                    "duration": ban_duration,
                    "expires_at": expires_at.isoformat() if expires_at else None,
                    "issued_at": ban.issued_at.isoformat()
                }
            }
        }

    @staticmethod
    async def ban_player_temporary(
        db: Session,
        server: Server,
        player_identifier: str,
        reason: str,
        duration_type: str,  # "hours", "days", "weeks", "months"
        duration_value: int,
        issued_by: str = "Console"
    ) -> Dict[str, Any]:
        """Ban a player temporarily"""
        if duration_type not in ["hours", "days", "weeks", "months"]:
            return {
                "success": False,
                "message": f"Invalid duration type: {duration_type}. Use: hours, days, weeks, months"
            }
        
        if duration_value <= 0:
            return {
                "success": False,
                "message": "Duration value must be greater than 0"
            }
        
        return await PlayerService.ban_player(
            db, server, player_identifier, reason,
            duration_type, duration_value, issued_by
        )

    @staticmethod
    async def ban_player_permanent(
        db: Session,
        server: Server,
        player_identifier: str,
        reason: str,
        issued_by: str = "Console"
    ) -> Dict[str, Any]:
        """Ban a player permanently"""
        return await PlayerService.ban_player(
            db, server, player_identifier, reason,
            "permanent", 0, issued_by
        )

    @staticmethod
    async def unban_player(
        db: Session,
        server: Server,
        player_identifier: str,
        issued_by: str = "Console"
    ) -> Dict[str, Any]:
        """Unban a player"""
        
        # Find player
        player = PlayerService.get_player_by_uuid(db, server, player_identifier)
        if not player:
            player = PlayerService.get_player_by_name(db, server, player_identifier)
        
        if not player:
            return {
                "success": False,
                "message": f"Player '{player_identifier}' not found",
                "error": "PLAYER_NOT_FOUND"
            }
        
        # Find active bans
        active_bans = db.query(PlayerBan).filter(
            PlayerBan.player_uuid == player.uuid,
            PlayerBan.server_id == server.id,
            PlayerBan.is_active == True
        ).all()
        
        if not active_bans:
            return {
                "success": False,
                "message": f"Player '{player.name}' has no active bans"
            }
        
        # Mark all active bans as inactive
        for ban in active_bans:
            ban.is_active = False
        
        # Execute unban command on server
        process = server_service.get_process(server.name)
        if process and process.is_running():
            await process.write(f"pardon {player.name}")

        # Also notify via Bridge if connected
        from routes.bridge import manager as bridge_manager
        from database.models.user import User
        owner = db.query(User).filter(User.id == server.user_id).first()
        if owner:
            await bridge_manager.send_unban(owner.username, player.name)
        
        db.commit()
        
        # Audit log
        BitacoraService.add_log(
            db,
            issued_by,
            "PLAYER_UNBAN",
            f"Unbanned player {player.name} ({player.uuid})"
        )
        
        return {
            "success": True,
            "message": f"Player '{player.name}' has been unbanned",
            "player": {
                "uuid": player.uuid,
                "name": player.name
            }
        }

    @staticmethod
    async def kick_player(
        db: Session,
        server: Server,
        player_identifier: str,
        reason: str = "You have been kicked from the server",
        issued_by: str = "Console"
    ) -> Dict[str, Any]:
        """
        Kick a player from the server (temporary removal, not permanent ban)
        """
        
        # Find player (could be online player not yet in DB)
        player = PlayerService.get_player_by_uuid(db, server, player_identifier)
        if not player:
            player = PlayerService.get_player_by_name(db, server, player_identifier)
        
        if not player:
            # If player not in DB, still try to kick if online
            online_players = PlayerService.get_online_players(server.name)
            online_names = [p.get('username', p.get('name')) for p in online_players]
            
            if player_identifier not in online_names:
                return {
                    "success": False,
                    "message": f"Player '{player_identifier}' not found",
                    "error": "PLAYER_NOT_FOUND"
                }
            
            player_name = player_identifier
        else:
            player_name = player.name
        
        # Execute kick command on server
        process = server_service.get_process(server.name)
        if not process or not process.is_running():
            return {
                "success": False,
                "message": f"Server '{server.name}' is not running",
                "error": "SERVER_OFFLINE"
            }
        
        await process.write(f"kick {player_name} {reason}")

        # Also notify via Bridge if connected
        from routes.bridge import manager as bridge_manager
        from database.models.user import User
        owner = db.query(User).filter(User.id == server.user_id).first()
        if owner:
            await bridge_manager.send_kick(owner.username, player_name, reason)
        
        # Audit log
        if player:
            BitacoraService.add_log(
                db,
                issued_by,
                "PLAYER_KICK",
                f"Kicked player {player.name} ({player.uuid}): {reason}"
            )
        else:
            BitacoraService.add_log(
                db,
                issued_by,
                "PLAYER_KICK",
                f"Kicked player {player_name}: {reason}"
            )
        
        return {
            "success": True,
            "message": f"Player '{player_name}' has been kicked",
            "player": {
                "name": player_name,
                "uuid": player.uuid if player else None,
                "reason": reason
            }
        }

    @staticmethod
    async def ban_ip(
        db: Session,
        server: Server,
        ip_address: str,
        reason: str,
        duration_type: str = "permanent",
        duration_value: int = 0,
        issued_by: str = "Console"
    ) -> Dict[str, Any]:
        """
        Ban an IP address
        """
        
        # Validate IP format (basic)
        ip_parts = ip_address.split('.')
        if len(ip_parts) != 4:
            return {
                "success": False,
                "message": f"Invalid IP address format: {ip_address}",
                "error": "INVALID_IP"
            }
        
        try:
            for part in ip_parts:
                num = int(part)
                if num < 0 or num > 255:
                    raise ValueError
        except (ValueError, AttributeError):
            return {
                "success": False,
                "message": f"Invalid IP address format: {ip_address}",
                "error": "INVALID_IP"
            }
        
        # Execute ban-ip command on server
        process = server_service.get_process(server.name)
        if process and process.is_running():
            await process.write(f"ban-ip {ip_address} {reason}")
        
        # Audit log
        ban_duration = (
            "permanent" if duration_type == "permanent"
            else f"{duration_value} {duration_type}"
        )
        BitacoraService.add_log(
            db,
            issued_by,
            "IP_BAN",
            f"Banned IP {ip_address} for {ban_duration}: {reason}"
        )
        
        return {
            "success": True,
            "message": f"IP address '{ip_address}' has been banned",
            "ip": {
                "address": ip_address,
                "reason": reason,
                "duration": ban_duration
            }
        }

    @staticmethod
    async def unban_ip(
        db: Session,
        server: Server,
        ip_address: str,
        issued_by: str = "Console"
    ) -> Dict[str, Any]:
        """
        Unban an IP address
        """
        
        # Validate IP format
        ip_parts = ip_address.split('.')
        if len(ip_parts) != 4:
            return {
                "success": False,
                "message": f"Invalid IP address format: {ip_address}",
                "error": "INVALID_IP"
            }
        
        # Execute pardon-ip command
        process = server_service.get_process(server.name)
        if process and process.is_running():
            await process.write(f"pardon-ip {ip_address}")

        # Also notify via Bridge if connected
        from routes.bridge import manager as bridge_manager
        from database.models.user import User
        owner = db.query(User).filter(User.id == server.user_id).first()
        if owner:
            if owner.username in bridge_manager.active_connections:
                await bridge_manager.active_connections[owner.username].send_json({
                    "action": "unban-ip",
                    "ip": ip_address
                })
        
        # Audit log
        BitacoraService.add_log(
            db,
            issued_by,
            "IP_UNBAN",
            f"Unbanned IP {ip_address}"
        )
        
        return {
            "success": True,
            "message": f"IP address '{ip_address}' has been unbanned",
            "ip": {
                "address": ip_address
            }
        }

    @staticmethod
    def get_player_bans(
        db: Session,
        server: Server,
        player_identifier: str
    ) -> Dict[str, Any]:
        """Get all bans for a specific player"""
        
        # Find player
        player = PlayerService.get_player_by_uuid(db, server, player_identifier)
        if not player:
            player = PlayerService.get_player_by_name(db, server, player_identifier)
        
        if not player:
            return {
                "success": False,
                "message": f"Player '{player_identifier}' not found",
                "error": "PLAYER_NOT_FOUND"
            }
        
        # Get all bans
        bans = db.query(PlayerBan).filter(
            PlayerBan.player_uuid == player.uuid,
            PlayerBan.server_id == server.id
        ).all()
        
        ban_list = []
        for ban in bans:
            ban_entry = {
                "id": ban.id,
                "reason": ban.reason,
                "issued_by": ban.source,
                "issued_at": ban.issued_at.isoformat(),
                "is_active": ban.is_active,
                "expires_at": ban.expires_at.isoformat() if ban.expires_at else None,
                "is_permanent": ban.expires_at is None
            }
            ban_list.append(ban_entry)
        
        return {
            "success": True,
            "player": {
                "uuid": player.uuid,
                "name": player.name
            },
            "bans": ban_list,
            "active_bans": sum(1 for b in bans if b.is_active),
            "total_bans": len(bans)
        }

    @staticmethod
    def get_active_bans(db: Session, server: Server) -> Dict[str, Any]:
        """Get all currently active bans on a server"""
        
        active_bans = db.query(PlayerBan).filter(
            PlayerBan.server_id == server.id,
            PlayerBan.is_active == True
        ).all()
        
        bans_list = []
        now = datetime.datetime.utcnow()
        
        for ban in active_bans:
            # Check if ban has expired
            if ban.expires_at and ban.expires_at < now:
                ban.is_active = False
                continue
            
            player = db.query(Player).filter(
                Player.uuid == ban.player_uuid,
                Player.server_id == server.id
            ).first()
            
            bans_list.append({
                "player": {
                    "uuid": ban.player_uuid,
                    "name": player.name if player else "Unknown"
                },
                "reason": ban.reason,
                "issued_by": ban.source,
                "issued_at": ban.issued_at.isoformat(),
                "expires_at": ban.expires_at.isoformat() if ban.expires_at else None,
                "is_permanent": ban.expires_at is None
            })
        
        return {
            "success": True,
            "server": server.name,
            "active_bans_count": len(bans_list),
            "bans": bans_list
        }

    @staticmethod
    def check_if_banned(
        db: Session,
        server: Server,
        player_identifier: str
    ) -> Dict[str, Any]:
        """Check if a player is currently banned"""
        
        # Find player
        player = PlayerService.get_player_by_uuid(db, server, player_identifier)
        if not player:
            player = PlayerService.get_player_by_name(db, server, player_identifier)
        
        if not player:
            return {
                "success": True,
                "banned": False,
                "message": "Player not found in database"
            }
        
        # Check for active bans
        now = datetime.datetime.utcnow()
        active_ban = db.query(PlayerBan).filter(
            PlayerBan.player_uuid == player.uuid,
            PlayerBan.server_id == server.id,
            PlayerBan.is_active == True
        ).first()
        
        if active_ban:
            # Check if expired
            if active_ban.expires_at and active_ban.expires_at < now:
                active_ban.is_active = False
                db.commit()
                return {
                    "success": True,
                    "banned": False,
                    "message": "Ban has expired"
                }
            
            return {
                "success": True,
                "banned": True,
                "player": {
                    "uuid": player.uuid,
                    "name": player.name
                },
                "ban": {
                    "reason": active_ban.reason,
                    "issued_by": active_ban.source,
                    "issued_at": active_ban.issued_at.isoformat(),
                    "expires_at": active_ban.expires_at.isoformat() if active_ban.expires_at else None,
                    "is_permanent": active_ban.expires_at is None
                }
            }
        
        return {
            "success": True,
            "banned": False,
            "player": {
                "uuid": player.uuid,
                "name": player.name
            }
        }
