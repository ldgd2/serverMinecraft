"""
Player Auth Routes — /api/v1/player-auth/
Handles authentication and profiles for Minecraft Launcher players.
This is separate from the admin /auth/ routes.
"""
import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from database.connection import get_db
from database.models.players.player_account import PlayerAccount
from database.models.players.player_account_achievement import PlayerAccountAchievement
from database.models.players.player import Player
from database.models.server import Server
from database.models.players.player_stat import PlayerStat
from database.models.players.player_achievement import PlayerAchievement
from app.services.auth_service import get_password_hash, verify_password, create_access_token, generate_offline_uuid
from core.responses import APIResponse

router = APIRouter(prefix="/player-auth", tags=["Player Auth"])

# ─── Schemas ─────────────────────────────────────────────────────────────────

class PlayerRegisterRequest(BaseModel):
    username: str
    password: str
    birthday: Optional[str] = None

class PlayerLoginRequest(BaseModel):
    username: str
    password: str

class PremiumLoginRequest(BaseModel):
    username_oficial: str
    uuid_oficial: str
    minecraft_access_token: Optional[str] = ""
    microsoft_refresh_token: Optional[str] = ""

class StatUpdateRequest(BaseModel):
    server_name: str
    kills: Optional[int] = 0
    player_kills: Optional[int] = 0
    hostile_kills: Optional[int] = 0
    passive_kills: Optional[int] = 0
    deaths: Optional[int] = 0
    blocks_broken: Optional[int] = 0
    blocks_placed: Optional[int] = 0
    playtime_seconds: Optional[int] = 0
    kill_streak: Optional[int] = 0
    highlights: Optional[List[str]] = []

class HighlightAddRequest(BaseModel):
    description: str
    server_name: str
    icon: Optional[str] = "🔥"

class AchievementUnlockRequest(BaseModel):
    server_name: str
    achievement_key: str
    name: str
    description: Optional[str] = ""
    icon: Optional[str] = "🏆"

# ─── Token dependency ─────────────────────────────────────────────────────────

import re
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from app.services.auth_service import SECRET_KEY, ALGORITHM

_bearer = HTTPBearer(auto_error=False)

def get_current_player(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: Session = Depends(get_db),
) -> PlayerAccount:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        player_id: int = payload.get("player_id")
        if player_id is None:
            raise HTTPException(status_code=401, detail="Invalid player token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid player token")

    account = db.query(PlayerAccount).filter(PlayerAccount.id == player_id, PlayerAccount.is_active == True).first()
    if not account:
        raise HTTPException(status_code=401, detail="Player account not found or inactive")
    return account

def _create_player_token(account: PlayerAccount) -> str:
    return create_access_token(data={"sub": account.username, "player_id": account.id, "type": "player"})

# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/register")
def register_player(data: PlayerRegisterRequest, db: Session = Depends(get_db)):
    """Register a new no-premium player account."""
    username = data.username.strip()
    if len(username) < 3 or len(username) > 16:
        raise HTTPException(status_code=400, detail="Username must be 3-16 characters")

    existing = db.query(PlayerAccount).filter(PlayerAccount.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    account = PlayerAccount(
        username=username,
        hashed_password=get_password_hash(data.password),
        uuid=generate_offline_uuid(username),  # Correct Minecraft Offline UUID
        account_type="nopremium",
        birthday=data.birthday
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    token = _create_player_token(account)
    return APIResponse(status="success", message="Account created", data={
        "access_token": token,
        "token_type": "bearer",
        "username": account.username,
        "uuid": account.uuid,
        "account_type": account.account_type,
        "birthday": account.birthday
    })


@router.post("/login")
def login_player(data: PlayerLoginRequest, db: Session = Depends(get_db)):
    """Login for no-premium players."""
    account = db.query(PlayerAccount).filter(PlayerAccount.username == data.username).first()
    if not account or not account.hashed_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(data.password, account.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if account.is_banned:
        raise HTTPException(status_code=403, detail=f"Account banned: {account.ban_reason or 'Contact admin'}")
    if not account.is_active:
        raise HTTPException(status_code=403, detail="Account inactive")

    # Migration: Ensure UUID is correct for no-premium players
    if account.account_type == "nopremium":
        correct_uuid = generate_offline_uuid(account.username)
        if account.uuid != correct_uuid:
            account.uuid = correct_uuid
            
    account.last_login_at = datetime.datetime.utcnow()
    db.commit()

    token = _create_player_token(account)
    return APIResponse(status="success", message="Login successful", data={
        "access_token": token,
        "token_type": "bearer",
        "username": account.username,
        "uuid": account.uuid,
        "account_type": account.account_type,
        "birthday": account.birthday
    })


@router.post("/login/premium")
def login_premium_player(data: PremiumLoginRequest, db: Session = Depends(get_db)):
    """
    Register/Login a premium (Microsoft) player.
    Called from the launcher after a successful Microsoft OAuth flow.
    """
    account = db.query(PlayerAccount).filter(
        (PlayerAccount.uuid == data.uuid_oficial) | (PlayerAccount.username == data.username_oficial)
    ).first()

    if not account:
        # Auto-create on first premium login
        account = PlayerAccount(
            username=data.username_oficial,
            uuid=data.uuid_oficial,
            account_type="premium",
            microsoft_refresh_token=data.microsoft_refresh_token,
            minecraft_access_token=data.minecraft_access_token,
        )
        db.add(account)
    else:
        # Update tokens
        account.username = data.username_oficial
        account.uuid = data.uuid_oficial
        account.account_type = "premium"
        account.microsoft_refresh_token = data.microsoft_refresh_token
        account.minecraft_access_token = data.minecraft_access_token
        account.last_login_at = datetime.datetime.utcnow()

    db.commit()
    db.refresh(account)

    token = _create_player_token(account)
    return APIResponse(status="success", message="Premium login successful", data={
        "access_token": token,
        "token_type": "bearer",
        "username": account.username,
        "uuid": account.uuid,
        "account_type": account.account_type,
        "birthday": account.birthday
    })
class BirthdayUpdateRequest(BaseModel):
    birthday: str

@router.post("/update-birthday")
def update_birthday(data: BirthdayUpdateRequest, current_player: PlayerAccount = Depends(get_current_player), db: Session = Depends(get_db)):
    """Update the birthday for the current player (used mainly for premium players)."""
    current_player.birthday = data.birthday
    db.commit()
    return APIResponse(status="success", message="Birthday updated")


@router.get("/profile")
def get_player_profile(current: PlayerAccount = Depends(get_current_player), db: Session = Depends(get_db)):
    """Get the current player's profile, stats and achievements."""
    # Hostile mobs for K/D calculation
    HOSTILE_MOBS = {
        "zombie", "skeleton", "creeper", "spider", "enderman", "witch", "slime", "silverfish",
        "ghast", "blaze", "magma_cube", "endermite", "guardian", "shulker", "husk", "stray",
        "wither_skeleton", "vex", "evoker", "vindicator", "pillager", "ravager", "hoglin",
        "zoglin", "piglin_brute", "warden", "drowned", "phantom", "wither", "ender_dragon", 
        "elder_guardian", "ravager"
    }

    # Aggregate server stats for this player (by username or UUID)
    from sqlalchemy import func
    db_players = db.query(Player).filter(
        (Player.uuid == current.uuid) | (func.lower(Player.name) == func.lower(current.username))
    ).all()
    
    # Aggregating Stats
    server_stats = []
    total_server_playtime = 0
    total_server_kills = 0
    total_server_deaths = 0
    total_server_blocks_broken = 0
    total_server_blocks_placed = 0
    
    # K/D Specific Categories
    total_server_player_kills = 0
    total_server_hostile_kills = 0
    total_server_passive_kills = 0

    for p in db_players:
        if p.detail:
            total_server_playtime += p.detail.total_playtime_seconds or 0
        
        # Track seen keys in this server to avoid double counting if total_kill is present
        seen_entity_kills = 0
        
        for s in p.stats:
            # Aggregate kills
            if s.stat_key.startswith("kill:"):
                # Format is usually kill:entity_name or kill:minecraft:entity_name
                parts = s.stat_key.split(":")
                entity = parts[-1].lower()
                
                if entity == "player":
                    total_server_player_kills += s.stat_value
                elif entity in HOSTILE_MOBS:
                    total_server_hostile_kills += s.stat_value
                else:
                    total_server_passive_kills += s.stat_value
                
                seen_entity_kills += s.stat_value
                total_server_kills += s.stat_value
            
            elif s.stat_key == "total_kill":
                # Only add if we haven't counted detailed kills, or handle separately
                # For now, if we have detailed kills, they are more accurate
                pass
            
            # Aggregate deaths
            elif s.stat_key == "total_death" or s.stat_key.startswith("death"):
                total_server_deaths += s.stat_value

            # Aggregate blocks broken
            elif s.stat_key == "total_block_broken" or s.stat_key.startswith("block_broken"):
                total_server_blocks_broken += s.stat_value
                
            # Aggregate blocks placed
            elif s.stat_key == "total_block_placed" or s.stat_key.startswith("block_placed"):
                total_server_blocks_placed += s.stat_value

        server_stats.append({
            "server_id": p.server_id,
            "server_name": p.server.name if p.server else "Unknown",
            "playtime_seconds": p.detail.total_playtime_seconds if p.detail else 0,
        })

    # Merging Achievements
    achievements = []
    
    # Global Account Achievements
    for a in current.achievements:
        achievements.append({
            "key": a.achievement_key,
            "name": a.name,
            "description": a.description,
            "icon": a.icon,
            "unlocked_at": a.unlocked_at.isoformat() if a.unlocked_at else None,
            "server_name": a.server_name or "Global",
        })
        
    # Server Specific Achievements (from Mod)
    for p in db_players:
        for sa in p.achievements:
            achievements.append({
                "key": sa.achievement_id,
                "name": sa.name,
                "description": sa.description,
                "icon": "🏆",
                "unlocked_at": sa.unlocked_at.isoformat() if sa.unlocked_at else None,
                "server_name": p.server.name if p.server else "Servidor",
            })

    # Final Totals (Account + Server detailed)
    # We assume current.total_kills is the 'legacy' or global count from launcher pushes
    final_kills = current.total_kills + total_server_kills
    final_player_kills = current.total_player_kills + total_server_player_kills
    final_hostile_kills = current.total_hostile_kills + total_server_hostile_kills
    
    # Genocide score is the total sum of all kills (Player + Hostile + Passive)
    final_genocide = current.total_genocide_score + total_server_kills
    
    final_deaths = current.total_deaths + total_server_deaths
    final_blocks_broken = current.total_blocks_broken + total_server_blocks_broken
    final_blocks_placed = current.total_blocks_placed + total_server_blocks_placed
    total_pt = current.total_playtime_seconds + total_server_playtime

    # K/D Calculation (Balanced)
    # Kills = (Hostile Mobs) + (Players * 10)
    weighted_kills = final_hostile_kills + (final_player_kills * 10)
    kd_ratio = round(weighted_kills / max(final_deaths, 1), 2)
    
    # Genocida Score (All kills: passive + hostile + players)
    # Already calculated as final_genocide

    h = total_pt // 3600
    m = (total_pt % 3600) // 60

    return APIResponse(status="success", message="Profile retrieved", data={
        "username": current.username,
        "uuid": current.uuid,
        "account_type": current.account_type,
        "member_since": current.created_at.isoformat(),
        "last_login": current.last_login_at.isoformat() if current.last_login_at else None,
        "stats": {
            "playtime": f"{h}h {m}m",
            "playtime_seconds": total_pt,
            "kills": final_kills,
            "deaths": final_deaths,
            "kd_ratio": kd_ratio,
            "genocida": final_genocide,
            "player_kills": final_player_kills,
            "hostile_kills": final_hostile_kills,
            "blocks_broken": final_blocks_broken,
            "blocks_placed": final_blocks_placed,
            "best_kill_streak": current.best_kill_streak,
        },
        "achievements": achievements,
        "highlights": current.highlights or [],
        "servers_played": len(server_stats),
    })


@router.post("/stats/update")
def update_player_stats(
    data: StatUpdateRequest,
    current: PlayerAccount = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    """
    Called by the launcher (or a plugin) to push updated stats from a gaming session.
    Accumulates on top of existing values.
    """
    current.total_kills += data.kills
    current.total_player_kills += data.player_kills
    current.total_hostile_kills += data.hostile_kills
    
    # Calculate genocide score for this session update
    # If detailed ones are provided, we use them, otherwise we just use 'kills' as passive or unknown
    session_genocide = data.player_kills + data.hostile_kills + data.passive_kills
    if session_genocide == 0 and data.kills > 0:
        session_genocide = data.kills
        
    current.total_genocide_score += session_genocide
    
    current.total_deaths += data.deaths
    current.total_blocks_broken += data.blocks_broken
    current.total_blocks_placed += data.blocks_placed
    current.total_playtime_seconds += data.playtime_seconds
    if data.kill_streak > current.best_kill_streak:
        current.best_kill_streak = data.kill_streak

    # Handle highlights (simple list of strings for now)
    # This could be more complex later
    
    db.commit()

    # Auto-unlock achievements based on stats
    _check_and_grant_achievements(current, data.server_name, db)

    return APIResponse(status="success", message="Stats updated", data=None)

@router.post("/highlights/add")
def add_highlight(
    data: HighlightAddRequest,
    current: PlayerAccount = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    """Add a new highlight or 'best play' to the player's profile."""
    if not current.highlights:
        current.highlights = []
    
    # We'll just store them as formatted strings for now
    highlight_str = f"[{data.server_name}] {data.icon} {data.description} ({datetime.datetime.now().strftime('%d/%m/%Y')})"
    
    # Keep only last 10 highlights
    new_highlights = [highlight_str] + (current.highlights or [])
    current.highlights = new_highlights[:10]
    
    db.commit()
    return APIResponse(status="success", message="Highlight added", data=current.highlights)


@router.post("/achievements/unlock")
def unlock_achievement(
    data: AchievementUnlockRequest,
    current: PlayerAccount = Depends(get_current_player),
    db: Session = Depends(get_db)
):
    """Manually unlock an achievement for the current player."""
    existing = db.query(PlayerAccountAchievement).filter(
        PlayerAccountAchievement.account_id == current.id,
        PlayerAccountAchievement.achievement_key == data.achievement_key
    ).first()

    if existing:
        return APIResponse(status="success", message="Achievement already unlocked", data=None)

    achievement = PlayerAccountAchievement(
        account_id=current.id,
        achievement_key=data.achievement_key,
        name=data.name,
        description=data.description,
        icon=data.icon,
        server_name=data.server_name,
    )
    db.add(achievement)
    db.commit()

    return APIResponse(status="success", message=f"Achievement unlocked: {data.name}", data={
        "key": data.achievement_key,
        "name": data.name,
        "icon": data.icon,
    })


@router.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    """Top 20 players by kills."""
    top = db.query(PlayerAccount).filter(
        PlayerAccount.is_active == True,
        PlayerAccount.is_banned == False
    ).order_by(PlayerAccount.total_kills.desc()).limit(20).all()

    return APIResponse(status="success", message="Leaderboard", data=[{
        "rank": i + 1,
        "username": p.username,
        "account_type": p.account_type,
        "kills": p.total_kills,
        "deaths": p.total_deaths,
        "kd_ratio": round((p.total_hostile_kills + (p.total_player_kills * 10)) / max(p.total_deaths, 1), 2),
        "genocida": p.total_genocide_score,
        "playtime_hours": round(p.total_playtime_seconds / 3600, 1),
        "achievements_count": len(p.achievements),
    } for i, p in enumerate(top)])

@router.get("/leaderboard/{category}")
def get_leaderboard_by_category(category: str, db: Session = Depends(get_db)):
    """Get leaderboard by specific category (kills, blocks, playtime)."""
    query = db.query(PlayerAccount).filter(
        PlayerAccount.is_active == True,
        PlayerAccount.is_banned == False
    )
    
    if category == "blocks":
        query = query.order_by(PlayerAccount.total_blocks_broken.desc())
    elif category == "playtime":
        query = query.order_by(PlayerAccount.total_playtime_seconds.desc())
    elif category == "genocida":
        query = query.order_by(PlayerAccount.total_genocide_score.desc())
    else:
        query = query.order_by(PlayerAccount.total_kills.desc())
        
    top = query.limit(20).all()

    return APIResponse(status="success", message=f"Leaderboard for {category}", data=[{
        "rank": i + 1,
        "username": p.username,
        "account_type": p.account_type,
        "kills": p.total_kills,
        "blocks": p.total_blocks_broken,
        "genocida": p.total_genocide_score,
        "playtime_hours": round(p.total_playtime_seconds / 3600, 1),
        "achievements_count": len(p.achievements),
    } for i, p in enumerate(top)])


# ─── Internal helper ──────────────────────────────────────────────────────────

def _check_and_grant_achievements(account: PlayerAccount, server_name: str, db: Session):
    """Check and auto-grant stat-based achievements."""
    candidates = []

    if account.total_kills >= 1:
        candidates.append(("first_blood", "Primera Sangre", "Consigue tu primera kill", "⚔️"))
    if account.total_kills >= 10:
        candidates.append(("10_kills", "Guerrero", "Alcanza 10 kills", "🗡️"))
    if account.total_kills >= 100:
        candidates.append(("100_kills", "Asesino", "Alcanza 100 kills", "💀"))
    if account.total_blocks_broken >= 100:
        candidates.append(("miner_100", "Minero", "Rompe 100 bloques", "⛏️"))
    if account.total_blocks_broken >= 1000:
        candidates.append(("miner_1k", "Minero Experto", "Rompe 1000 bloques", "💎"))
    if account.total_playtime_seconds >= 3600:
        candidates.append(("1h_playtime", "Dedicado", "1 hora de juego", "⏰"))
    if account.total_playtime_seconds >= 36000:
        candidates.append(("10h_playtime", "Veterano", "10 horas de juego", "🏅"))
    if account.best_kill_streak >= 5:
        candidates.append(("streak_5", "En Racha", "5 kills seguidas", "🔥"))

    for key, name, desc, icon in candidates:
        exists = db.query(PlayerAccountAchievement).filter(
            PlayerAccountAchievement.account_id == account.id,
            PlayerAccountAchievement.achievement_key == key
        ).first()
        if not exists:
            db.add(PlayerAccountAchievement(
                account_id=account.id,
                achievement_key=key,
                name=name,
                description=desc,
                icon=icon,
                server_name=server_name,
            ))
    db.commit()
