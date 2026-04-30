
import os
import json
import logging
from sqlalchemy.orm import Session
from database.models.players.player_stat import PlayerStat
from database.models.players.player_achievement import PlayerAchievement

logger = logging.getLogger(__name__)

class PlayerStatsSyncer:
    def __init__(self, server_path: str, server_id: int):
        self.server_path = server_path
        self.server_id = server_id

    def sync_player_stats(self, db: Session, player_uuid: str):
        """
        Reads stats and advancements from the world folder and updates the DB.
        """
        # 1. Stats (stats/uuid.json)
        # Location: world/stats/uuid.json (Standard) or just "stats" in server root sometimes?
        # Usually it's in the default level-name folder.
        
        # We need to find the world folder.
        # Assuming server.properties "level-name"
        level_name = "world"
        props_path = os.path.join(self.server_path, "server.properties")
        if os.path.exists(props_path):
            try:
                with open(props_path, "r") as f:
                    for line in f:
                        if line.strip().startswith("level-name="):
                            level_name = line.strip().split("=")[1]
            except: pass
            
        world_dir = os.path.join(self.server_path, level_name)
        stats_file = os.path.join(world_dir, "stats", f"{player_uuid}.json")
        
        if os.path.exists(stats_file):
            try:
                self._sync_stats_file(db, player_uuid, stats_file)
            except Exception as e:
                logger.error(f"Failed to sync stats for {player_uuid}: {e}")

        # 2. Advancements (advancements/uuid.json)
        adv_file = os.path.join(world_dir, "advancements", f"{player_uuid}.json")
        if os.path.exists(adv_file):
             try:
                self._sync_advancements_file(db, player_uuid, adv_file)
             except Exception as e:
                logger.error(f"Failed to sync advancements for {player_uuid}: {e}")

    def _sync_stats_file(self, db: Session, player_uuid: str, stats_file: str):
        with open(stats_file, 'r') as f:
            data = json.load(f)
            
        stats_data = data.get("stats", {})
        
        # Flatten stats
        # Format: {"minecraft:custom": {"minecraft:jump": 10}, "minecraft:mined": {...}}
        
        # We want to store key="mined.stone", value=10
        # or key="custom.jump", value=10
        
        for category, items in stats_data.items():
            cat_name = category.replace("minecraft:", "")
            for stat_key, value in items.items():
                s_key = stat_key.replace("minecraft:", "")
                full_key = f"{cat_name}.{s_key}"
                
                # Check exist
                stat_entry = db.query(PlayerStat).filter_by(
                    player_uuid=player_uuid,
                    server_id=self.server_id,
                    stat_key=full_key
                ).first()
                
                if stat_entry:
                    stat_entry.stat_value = value
                else:
                    new_stat = PlayerStat(
                        player_uuid=player_uuid,
                        server_id=self.server_id,
                        stat_key=full_key,
                        stat_value=value
                    )
                    db.add(new_stat)
        
        db.commit()

    def _sync_advancements_file(self, db: Session, player_uuid: str, adv_file: str):
        with open(adv_file, 'r') as f:
            data = json.load(f)
            
        # Format: {"minecraft:story/mine_stone": {"done": true, "criteria": {...}}}
        
        for adv_id, info in data.items():
            if not info.get("done", False):
                continue
                
            # Formatting ID
            clean_id = adv_id.replace("minecraft:", "")
            
            # Check exist
            entry = db.query(PlayerAchievement).filter_by(
                player_uuid=player_uuid, 
                server_id=self.server_id, 
                achievement_id=clean_id
            ).first()
            
            if not entry:
                # Try to get a pretty name/desc? Hard without mapping.
                # Just store ID for now.
                new_adv = PlayerAchievement(
                    player_uuid=player_uuid,
                    server_id=self.server_id,
                    achievement_id=clean_id,
                    name=clean_id.split("/")[-1].replace("_", " ").title()
                )
                db.add(new_adv)
        
        db.commit()
