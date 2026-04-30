from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.connection import get_db
from database.models.bitacora import Bitacora
from database.models.user import User
from routes.auth import get_current_user
from database.schemas import BitacoraEntry
from core.responses import APIResponse

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs")
def get_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=100),
    action: Optional[str] = None,
    user: Optional[str] = None,
    search: Optional[str] = None,
    server: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Bitacora)
    
    # Filters
    if action and action != "all" and action != "":
        query = query.filter(Bitacora.action == action)
        
    if user:
        query = query.filter(Bitacora.username.ilike(f"%{user}%"))
        
    if search:
        query = query.filter(Bitacora.details.ilike(f"%{search}%"))
        
    # Heuristic for server filter: search in details for server name
    if server:
        query = query.filter(Bitacora.details.ilike(f"%{server}%"))

    # Pagination stats
    total = query.count()
    total_pages = (total + limit - 1) // limit
    
    # Data
    logs = query.order_by(Bitacora.timestamp.desc()) \
                .offset((page - 1) * limit) \
                .limit(limit) \
                .all()
    return APIResponse(status="success", message="Audit logs retrieved", data={
        "items": logs,
        "total": total,
        "page": page,
        "pages": total_pages
    })
