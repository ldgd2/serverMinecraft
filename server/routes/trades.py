from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models.trade import Trade, CounterOffer
from app.controllers.server_controller import ServerController
from core.responses import APIResponse
from core.broadcaster import broadcaster
import json

router = APIRouter(prefix="/trades", tags=["Marketplace"])
server_controller = ServerController()

@router.post("/publish")
async def publish_trade(data: dict, db: Session = Depends(get_db)):
    """
    Publicar una venta.
    Data: { seller_uuid, seller_name, title, selling, asking }
    """
    seller_name = data.get("seller_name")
    title = data.get("title", "Venta de items")
    selling = data.get("selling")
    asking = data.get("asking")
    
    new_trade = Trade(
        seller_uuid=data.get("seller_uuid", "unknown"),
        seller_name=seller_name,
        title=title,
        selling_item=selling,
        asking_item=asking,
        status="OPEN"
    )
    db.add(new_trade)
    db.commit()
    db.refresh(new_trade)

    # Notificar anuncio global
    msg = f"§6[Market] §b{seller_name} §fha publicado: §e{title}"
    await server_controller.send_command("MinecraftTest", f'title @a actionbar {{"text":"{msg}"}}')
    await server_controller.send_command("MinecraftTest", f'tellraw @a {{"text":"{msg} . Pulsa \'.\' para ver."}}')
    
    return APIResponse(status="success", data=new_trade.id)

@router.get("/open")
def get_open_trades(db: Session = Depends(get_db)):
    trades = db.query(Trade).filter(Trade.status == "OPEN").all()
    # Convertir a dict manual para manejar JSON columns
    result = []
    for t in trades:
        result.append({
            "id": t.id,
            "title": t.title,
            "seller": t.seller_name,
            "selling": t.selling_item,
            "asking": t.asking_item
        })
    return APIResponse(status="success", data=result)

@router.post("/{trade_id}/counter-offer")
async def make_counter_offer(trade_id: int, data: dict, db: Session = Depends(get_db)):
    """
    Hacer una contra-oferta.
    Data: { buyer_uuid, buyer_name, offered_items: [...] }
    """
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade: raise HTTPException(status_code=404)
    
    new_offer = CounterOffer(
        trade_id=trade_id,
        buyer_uuid=data.get("buyer_uuid"),
        buyer_name=data.get("buyer_name"),
        offered_items=data.get("offered_items"),
        status="PENDING"
    )
    db.add(new_offer)
    db.commit()

    # Notificar al VENDEDOR
    notif = f"§6[Market] §b{new_offer.buyer_name} §fha enviado una contra-oferta por §e{trade.title}"
    await server_controller.send_command("MinecraftTest", f'tellraw {trade.seller_name} {{"text":"{notif}","color":"gold"}}')
    
    return APIResponse(status="success", message="Counter-offer sent")

@router.post("/resolve-offer/{offer_id}")
async def resolve_offer(offer_id: int, action: str, reason: str = None, db: Session = Depends(get_db)):
    """
    Acción sobre una contra-oferta específica.
    Action: 'accept' o 'reject'
    """
    offer = db.query(CounterOffer).filter(CounterOffer.id == offer_id).first()
    if not offer: raise HTTPException(status_code=404)
    
    trade = offer.trade

    if action == "accept":
        offer.status = "ACCEPTED"
        trade.status = "COMPLETED"
        # Notificar éxito
        msg = f"§6[Market] §a¡Oferta Aceptada! §fIntercambiando items..."
        await server_controller.send_command("MinecraftTest", f'tellraw {offer.buyer_name} {{"text":"{msg}"}}')
        await server_controller.send_command("MinecraftTest", f'tellraw {trade.seller_name} {{"text":"{msg}"}}')
        
        # Rechazar automáticamente otras ofertas para este trade
        db.query(CounterOffer).filter(CounterOffer.trade_id == trade.id, CounterOffer.id != offer_id).update({"status": "REJECTED", "rejection_reason": "Trade ya completado"})
        
    else:
        offer.status = "REJECTED"
        offer.rejection_reason = reason or "No me interesa, carajo"
        # Notificar al comprador
        msg = f"§6[Market] §cOferta Rechazada por {trade.seller_name}: §f{offer.rejection_reason}"
        await server_controller.send_command("MinecraftTest", f'tellraw {offer.buyer_name} {{"text":"{msg}"}}')

    db.commit()
    return APIResponse(status="success")
