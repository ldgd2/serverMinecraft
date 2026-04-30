"""
Service to sync MasterBridge data with database
"""
from sqlalchemy.orm import Session
from database.models.players.player import Player
from database.models.players.player_detail import PlayerDetail
from database.models.players.player_achievement import PlayerAchievement
from database.models.server import Server
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class MasterBridgeSyncService:
    """Service to synchronize MasterBridge API data with database"""
    
    @staticmethod
    def sync_players(db: Session, server_id: int, mb_players: List[Dict]) -> None:
        """
        Sync player data from MasterBridge to database
        
        Args:
            db: Database session
            server_id: ID of the server
            mb_players: List of player dictionaries from MasterBridge API
        """
        if not mb_players:
            return
            
        for player_data in mb_players:
            try:
                username = player_data.get('name')
                uuid = player_data.get('uuid')
                
                if not username or not uuid:
                    continue
                
                # Find or create player for this server
                player = db.query(Player).filter(
                    Player.uuid == uuid,
                    Player.server_id == server_id
                ).first()
                
                if not player:
                    player = Player(
                        uuid=uuid,
                        server_id=server_id,
                        name=username,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    db.add(player)
                    db.flush()  # Get the ID
                else:
                    # Update username and timestamp
                    player.name = username
                    player.updated_at = datetime.utcnow()
                    db.flush()
                
                # Update or create player details
                if not player.detail:
                    detail = PlayerDetail(
                        player_uuid=player.uuid,
                        player_server_id=player.server_id
                    )
                    db.add(detail)
                else:
                    detail = player.detail
                
                # Update from MasterBridge data
                detail.last_dimension = player_data.get('dimension', 'minecraft:overworld')
                detail.last_position = player_data.get('pos', '0, 0, 0')
                # Note: PlayerDetail might not have level field, check schema
                
                db.commit()
                
            except Exception as e:
                logger.error(f"Error syncing player {player_data.get('name')}: {e}")
                db.rollback()
    
    @staticmethod
    def sync_achievements(db: Session, server_id: int, mb_achievements: Dict[str, List[str]]) -> None:
        """
        Sync achievements from MasterBridge to database
        
        Args:
            db: Database session
            server_id: ID of the server
            mb_achievements: Dict mapping player names to achievement lists
        """
        if not mb_achievements:
            return
        
        for username, achievement_list in mb_achievements.items():
            try:
                # Find player by username and server
                player = db.query(Player).filter(
                    Player.name == username,
                    Player.server_id == server_id
                ).first()
                
                if not player:
                    continue
                
                # Sync achievements
                for achievement_name in achievement_list:
                    # Check if achievement already recorded
                    existing = db.query(PlayerAchievement).filter(
                        PlayerAchievement.player_uuid == player.uuid,
                        PlayerAchievement.player_server_id == player.server_id,
                        PlayerAchievement.achievement_name == achievement_name
                    ).first()
                    
                    if not existing:
                        new_achievement = PlayerAchievement(
                            player_uuid=player.uuid,
                            player_server_id=player.server_id,
                            achievement_name=achievement_name,
                            unlocked_at=datetime.utcnow()
                        )
                        db.add(new_achievement)
                
                db.commit()
                
            except Exception as e:
                logger.error(f"Error syncing achievements for {username}: {e}")
                db.rollback()

sync_service = MasterBridgeSyncService()

