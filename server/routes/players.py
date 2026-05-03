from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Server
from database.models.players.player import Player
from app.services.minecraft import server_service
from app.services.player_service import PlayerService
from app.schemas.player_schemas import (
    BanPlayerRequest,
    KickPlayerRequest,
    UnbanPlayerRequest,
    BanIPRequest,
    UnbanIPRequest
)
import datetime
from core.responses import APIResponse
from typing import Optional
from routes.auth import get_current_user

router = APIRouter(prefix="/players", tags=["players"])

# ==================== Helper Functions ====================

def get_server_by_name(db: Session, name: str):
    """Get server by name or raise 404 error"""
    server = db.query(Server).filter(Server.name == name).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server

# ==================== Endpoints ====================

@router.get("/{server_name}/list")
def get_players(server_name: str, db: Session = Depends(get_db)):
    """
    Get all players for a server (Online + History)
    
    Returns:
    - Online players count
    - Total unique players
    - List of all players with details
    """
    server = get_server_by_name(db, server_name)
    
    # Get Online Players from Service
    process = server_service.get_process(server_name)
    online_players = []
    if process:
        online_players = process.player_manager.get_players() # [{username, ip, joined_at, uuid}]
        
    # Get All Players from DB
    db_players = db.query(Player).filter(Player.server_id == server.id).all()
    
    # Merge Data
    result = []
    
    # Helper to find online status
    online_map = {p.get('username', p.get('name')): p for p in online_players}
    
    from core.skinrestorer_bridge import get_skin_base64_from_skinrestorer
    from core.skin_utils import extract_skin_url, download_and_crop_head
    import os, datetime as dt
    SKINRESTORER_DB = {
        'host': os.environ.get('SKINRESTORER_HOST', 'localhost'),
        'user': os.environ.get('SKINRESTORER_USER', 'root'),
        'password': os.environ.get('SKINRESTORER_PASS', ''),
        'database': os.environ.get('SKINRESTORER_DB', 'SkinRestorer')
    }
    for p in db_players:
        is_online = p.name in online_map
        online_info = online_map.get(p.name, {})
        detail = p.detail
        last_played = detail.last_joined_at if detail else None
        playtime_seconds = detail.total_playtime_seconds if detail and detail.total_playtime_seconds else 0
        hours = playtime_seconds // 3600
        minutes = (playtime_seconds % 3600) // 60
        seconds = playtime_seconds % 60
        playtime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        ban_status = PlayerService.check_if_banned(db, server, p.uuid)
        # --- Detección de Cuenta (Premium vs No-Premium/Launcher) ---
        # Mojang usa UUID v4. Los servidores offline usan UUID v3 (basado en nombre).
        # Un UUID v4 tiene un '4' en la posición 13: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
        is_premium_account = False
        if p.uuid and len(p.uuid) > 14 and p.uuid[14] == '4':
            is_premium_account = True

        # --- SkinHead y Sincronización ---
        head_url = None
        head_path = f"static/heads/{p.name}.png"
        
        # 1. Si ya existe el archivo físico, lo usamos
        if os.path.exists(head_path):
            head_url = f"/static/heads/{p.name}.png"
        else:
            # 2. Intentar obtener el Base64 de varias fuentes
            skin_base64 = None
            
            # Fuente A: SkinRestorer (Premium o skins manuales en el server)
            try:
                skin_base64 = get_skin_base64_from_skinrestorer(SKINRESTORER_DB, p.name)
            except: pass
            
            # Fuente B: Base de datos local (Sincronizado desde el Launcher)
            if not skin_base64 and detail:
                skin_base64 = detail.skin_base64
            
            # 3. Procesar el Base64 encontrado
            if skin_base64:
                # Mojang-style JSON?
                skin_url = extract_skin_url(skin_base64)
                if skin_url:
                    try:
                        download_and_crop_head(skin_url, head_path)
                        head_url = f"/static/heads/{p.name}.png"
                    except: pass
                else:
                    # Raw PNG Base64?
                    try:
                        from PIL import Image
                        from io import BytesIO
                        import base64 as b64
                        skin_img = Image.open(BytesIO(b64.b64decode(skin_base64))).convert('RGBA')
                        face = skin_img.crop((8, 8, 16, 16)).resize((64, 64), Image.NEAREST)
                        helmet = skin_img.crop((40, 8, 48, 16)).resize((64, 64), Image.NEAREST)
                        final_head = Image.alpha_composite(face, helmet)
                        os.makedirs("static/heads", exist_ok=True)
                        final_head.save(head_path)
                        head_url = f"/static/heads/{p.name}.png"
                    except: pass
            
            # 4. FALLBACK: Solo para jugadores Premium usamos APIs externas
            if not head_url and is_premium_account:
                head_url = f"https://mc-heads.net/avatar/{p.name}/64"

        result.append({
            "uuid": p.uuid,
            "name": p.name,
            "is_online": is_online,
            "is_premium": is_premium_account,
            "last_played": last_played,
            "total_playtime": playtime_str,
            "ip": detail.last_ip if detail else None,
            "country": detail.country if detail else None,
            "os": detail.os if detail else None,
            "skin_last_update": detail.skin_last_update.isoformat() if detail and detail.skin_last_update else None,
            "head_url": head_url,
            "is_banned": ban_status.get("banned", False)
        })
        
    # Sort: Online first, then by last_played
    result.sort(key=lambda x: (not x['is_online'], x['last_played'] or datetime.datetime.min), reverse=True)
    
    return APIResponse(status="success", message="Players retrieved", data={
        "server": server_name,
        "online_count": len(online_players),
        "total_unique": len(result),
        "players": result
    })

@router.get("/{server_name}/online")
def get_online_players(server_name: str, db: Session = Depends(get_db)):
    """
    Get only currently online players on a server
    
    Returns quick list of online players with their info
    """
    server = get_server_by_name(db, server_name)
    
    online_players = PlayerService.get_online_players(server_name)
    
    return APIResponse(
        status="success",
        message="Online players retrieved",
        data={
            "server": server_name,
            "online_count": len(online_players),
            "players": online_players
        }
    )

@router.get("/skin/{identifier}")
async def get_player_skin_data(identifier: str, db: Session = Depends(get_db)):
    """
    Endpoint público para que el Mod (Fabric) obtenga la skin.
    Acepta nombre o UUID. Si es premium y no tenemos data, intenta Mojang.
    """
    from database.models.players.player import Player
    from database.models.players.player_account import PlayerAccount
    import uuid
    import requests

    # 1. Buscar en perfiles de servidor (Player)
    player = None
    try:
        val = uuid.UUID(identifier)
        player = db.query(Player).filter(Player.uuid == str(val)).first()
    except ValueError:
        player = db.query(Player).filter(Player.name == identifier).first()

    # 2. Si no hay perfil de servidor, buscar en cuentas globales (Launcher)
    account = None
    if not player:
        try:
            val = uuid.UUID(identifier)
            account = db.query(PlayerAccount).filter(PlayerAccount.uuid == str(val)).first()
        except ValueError:
            account = db.query(PlayerAccount).filter(PlayerAccount.username == identifier).first()
    
    # 3. Determinar fuente de datos
    detail = player.detail if player else None
    
    # Si tenemos datos firmados (value/signature), los devolvemos
    if detail and detail.skin_value:
        return {"value": detail.skin_value, "signature": detail.skin_signature or ""}
    
    if account and account.skin_value:
        return {"value": account.skin_value, "signature": account.skin_signature or ""}

    # 4. Fallback Mojang para Premium
    # Un UUID v4 suele ser premium. O si la cuenta dice ser premium.
    target_uuid = player.uuid if player else (account.uuid if account else None)
    is_premium = False
    if target_uuid and len(target_uuid) > 14 and target_uuid[14] == '4':
        is_premium = True
    if account and account.account_type == "premium":
        is_premium = True

    if is_premium and target_uuid:
        # Limpiar guiones para la API de Mojang
        clean_uuid = target_uuid.replace("-", "")
        try:
            # Mojang Session Server
            res = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{clean_uuid}?unsigned=false", timeout=5)
            if res.status_code == 200:
                data = res.json()
                for prop in data.get("properties", []):
                    if prop.get("name") == "textures":
                        val = prop.get("value")
                        sig = prop.get("signature")
                        # Opcional: Cachear en la base de datos para la próxima vez
                        if detail:
                            detail.skin_value = val
                            detail.skin_signature = sig
                            db.commit()
                        elif account:
                            account.skin_value = val
                            account.skin_signature = sig
                            db.commit()
                        return {"value": val, "signature": sig}
        except: pass

    raise HTTPException(status_code=404, detail="Skin not found or not generated yet")

@router.get("/{server_name}/details/{player_identifier}")
def get_player_details(
    server_name: str,
    player_identifier: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed stats for a player (by UUID or name)
    
    Includes:
    - Basic info (name, UUID, first/last seen)
    - Playtime statistics
    - Achievements
    - Ban history
    """
    server = get_server_by_name(db, server_name)
    
    # Find player
    player = PlayerService.get_player_by_uuid(db, server, player_identifier)
    if not player:
        player = PlayerService.get_player_by_name(db, server, player_identifier)
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
        
    detail = player.detail
    stats = player.stats
    achievements = player.achievements
    bans = player.bans

    # Calculate Playtime
    playtime_seconds = detail.total_playtime_seconds if detail and detail.total_playtime_seconds else 0
    hours = playtime_seconds // 3600
    minutes = (playtime_seconds % 3600) // 60
    seconds = playtime_seconds % 60
    playtime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # Check if currently online
    online_players = PlayerService.get_online_players(server_name)
    is_online = any(p.get('username') == player.name or p.get('name') == player.name for p in online_players)

    # --- SkinRestorer y cabeza ---
    from core.skinrestorer_bridge import get_skin_base64_from_skinrestorer
    from core.skin_utils import extract_skin_url, download_and_crop_head
    import os, datetime as dt
    SKINRESTORER_DB = {
        'host': os.environ.get('SKINRESTORER_HOST', 'localhost'),
        'user': os.environ.get('SKINRESTORER_USER', 'root'),
        'password': os.environ.get('SKINRESTORER_PASS', ''),
        'database': os.environ.get('SKINRESTORER_DB', 'SkinRestorer')
    }
    skin_base64 = get_skin_base64_from_skinrestorer(SKINRESTORER_DB, player.name)
    skin_changed = False
    head_url = None
    if skin_base64:
        if not detail.skin_base64 or detail.skin_base64 != skin_base64:
            detail.skin_base64 = skin_base64
            detail.skin_last_update = dt.datetime.utcnow()
            skin_changed = True
            db.commit()
        skin_url = extract_skin_url(skin_base64)
        if skin_url:
            head_path = f"static/heads/{player.name}.png"
            if skin_changed or not os.path.exists(head_path):
                try:
                    download_and_crop_head(skin_url, head_path)
                except Exception:
                    head_path = None
            if head_path and os.path.exists(head_path):
                head_url = f"/static/heads/{player.name}.png"

    return APIResponse(status="success", message="Player details retrieved", data={
        "player": {
            "uuid": player.uuid,
            "name": player.name,
            "is_online": is_online,
            "first_seen": player.created_at.isoformat(),
            "last_seen": detail.last_joined_at.isoformat() if detail and detail.last_joined_at else None,
            "playtime": playtime_str,
            "playtime_seconds": playtime_seconds,
            "last_ip": detail.last_ip if detail else None,
            "country": detail.country if detail else None,
            "os": detail.os if detail else None,
            "skin_last_update": detail.skin_last_update.isoformat() if detail and detail.skin_last_update else None,
            "head_url": head_url
        },
        "stats": {s.stat_key: s.stat_value for s in stats} if stats else {},
        "achievements": [
            {
                "id": a.achievement_id,
                "name": a.name,
                "description": a.description,
                "unlocked_at": a.unlocked_at.isoformat() if a.unlocked_at else None
            }
            for a in achievements
        ] if achievements else [],
        "bans": [
            {
                "id": b.id,
                "active": b.is_active,
                "reason": b.reason,
                "issued_by": b.source,
                "issued_at": b.issued_at.isoformat(),
                "expires_at": b.expires_at.isoformat() if b.expires_at else None,
                "is_permanent": b.expires_at is None
            }
            for b in bans
        ] if bans else []
    })

# ==================== BAN Endpoints ====================

@router.post("/{server_name}/ban")
async def ban_player(
    server_name: str,
    request: BanPlayerRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Ban a player (temporary or permanent)
    
    Parameters:
    - player_identifier: UUID or player name
    - reason: Reason for ban
    - duration_type: "permanent", "hours", "days", "weeks", "months"
    - duration_value: Number of units (ignored if duration_type is "permanent")
    
    Examples:
    - Ban for 24 hours: duration_type="hours", duration_value=24
    - Ban for 7 days: duration_type="days", duration_value=7
    - Ban forever: duration_type="permanent"
    """
    server = get_server_by_name(db, server_name)
    
    result = await PlayerService.ban_player(
        db,
        server,
        request.player_identifier,
        request.reason,
        request.duration_type,
        request.duration_value,
        current_user.username
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return APIResponse(status="success", message=result.get("message"), data=result)

@router.post("/{server_name}/ban/temporary")
async def ban_player_temporary(
    server_name: str,
    player_identifier: str = Query(...),
    reason: str = Query(...),
    hours: int = Query(None),
    days: int = Query(None),
    weeks: int = Query(None),
    months: int = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Ban a player temporarily using query parameters
    
    Use one of: hours, days, weeks, or months
    Example: /ban/temporary?player_identifier=Steve&reason=Spam&days=7
    """
    server = get_server_by_name(db, server_name)
    
    # Determine duration
    duration_type = None
    duration_value = 0
    
    if hours:
        duration_type = "hours"
        duration_value = hours
    elif days:
        duration_type = "days"
        duration_value = days
    elif weeks:
        duration_type = "weeks"
        duration_value = weeks
    elif months:
        duration_type = "months"
        duration_value = months
    else:
        raise HTTPException(
            status_code=400,
            detail="Must specify one of: hours, days, weeks, or months"
        )
    
    result = await PlayerService.ban_player_temporary(
        db,
        server,
        player_identifier,
        reason,
        duration_type,
        duration_value,
        current_user.username
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return APIResponse(status="success", message=result.get("message"), data=result)

@router.post("/{server_name}/ban/permanent")
async def ban_player_permanent(
    server_name: str,
    player_identifier: str = Query(...),
    reason: str = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Ban a player permanently
    
    Example: /ban/permanent?player_identifier=Steve&reason=Hacking
    """
    server = get_server_by_name(db, server_name)
    
    result = await PlayerService.ban_player_permanent(
        db,
        server,
        player_identifier,
        reason,
        current_user.username
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return APIResponse(status="success", message=result.get("message"), data=result)

@router.post("/{server_name}/unban")
async def unban_player(
    server_name: str,
    request: UnbanPlayerRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Unban a player
    
    Parameters:
    - player_identifier: UUID or player name
    """
    server = get_server_by_name(db, server_name)
    
    result = await PlayerService.unban_player(
        db,
        server,
        request.player_identifier,
        current_user.username
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return APIResponse(status="success", message=result.get("message"), data=result)

@router.get("/{server_name}/bans/{player_identifier}")
def get_player_bans(
    server_name: str,
    player_identifier: str,
    db: Session = Depends(get_db)
):
    """
    Get all bans for a specific player
    
    Returns:
    - Active bans
    - Inactive bans
    - Ban history
    """
    server = get_server_by_name(db, server_name)
    
    result = PlayerService.get_player_bans(db, server, player_identifier)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    
    return APIResponse(status="success", message="Player bans retrieved", data=result)

@router.get("/{server_name}/bans")
def get_active_bans(
    server_name: str,
    db: Session = Depends(get_db)
):
    """
    Get all currently active bans on a server
    
    Returns list of all banned players
    """
    server = get_server_by_name(db, server_name)
    
    result = PlayerService.get_active_bans(db, server)
    
    return APIResponse(status="success", message="Active bans retrieved", data=result)

@router.get("/{server_name}/check-ban/{player_identifier}")
def check_if_banned(
    server_name: str,
    player_identifier: str,
    db: Session = Depends(get_db)
):
    """
    Check if a player is currently banned
    
    Returns:
    - banned: boolean
    - ban details (if banned)
    """
    server = get_server_by_name(db, server_name)
    
    result = PlayerService.check_if_banned(db, server, player_identifier)
    
    return APIResponse(status="success", message="Ban status checked", data=result)

# ==================== KICK Endpoints ====================

@router.post("/{server_name}/kick")
async def kick_player(
    server_name: str,
    request: KickPlayerRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Kick a player from the server (temporary removal, not permanent)
    
    Parameters:
    - player_identifier: UUID or player name
    - reason: Reason for kick
    """
    server = get_server_by_name(db, server_name)
    
    result = await PlayerService.kick_player(
        db,
        server,
        request.player_identifier,
        request.reason,
        current_user.username
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return APIResponse(status="success", message=result.get("message"), data=result)

@router.post("/{server_name}/kick-query")
async def kick_player_query(
    server_name: str,
    player_identifier: str = Query(...),
    reason: str = Query(default="You have been kicked from the server"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Kick a player using query parameters
    
    Example: /kick-query?player_identifier=Steve&reason=Spam
    """
    server = get_server_by_name(db, server_name)
    
    result = await PlayerService.kick_player(
        db,
        server,
        player_identifier,
        reason,
        current_user.username
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return APIResponse(status="success", message=result.get("message"), data=result)

# ==================== IP BAN Endpoints ====================

@router.post("/{server_name}/ban-ip")
async def ban_ip(
    server_name: str,
    request: BanIPRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Ban an IP address
    
    Parameters:
    - ip_address: IP to ban (e.g., "192.168.1.1")
    - reason: Reason for ban
    - duration_type: "permanent", "hours", "days", "weeks", "months"
    - duration_value: Number of units
    """
    server = get_server_by_name(db, server_name)
    
    result = await PlayerService.ban_ip(
        db,
        server,
        request.ip_address,
        request.reason,
        request.duration_type,
        request.duration_value,
        current_user.username
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return APIResponse(status="success", message=result.get("message"), data=result)

@router.post("/{server_name}/unban-ip")
async def unban_ip(
    server_name: str,
    request: UnbanIPRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Unban an IP address
    
    Parameters:
    - ip_address: IP to unban
    """
    server = get_server_by_name(db, server_name)
    
    result = await PlayerService.unban_ip(
        db,
        server,
        request.ip_address,
        current_user.username
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    
    return APIResponse(status="success", message=result.get("message"), data=result)
