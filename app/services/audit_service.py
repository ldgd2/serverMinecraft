from sqlalchemy.orm import Session
from database.models.bitacora import Bitacora
from database.models.user import User
import datetime

class AuditService:
    @staticmethod
    def log_action(db: Session, user: User, action: str, ip_address: str, details: str = None):
        """
        Logs a user action to the Bitacora (Audit Log).
        
        Args:
            db (Session): Database session
            user (User): The user performing the action (can be None for system actions, but usually required)
            action (str): Short description of the action (e.g., "START_SERVER")
            ip_address (str): IP address of the user
            details (str, optional): Detailed description or JSON payload of the change
        """
        try:
            username = user.username if user else "SYSTEM"
            
            entry = Bitacora(
                username=username,
                action=action,
                ip_address=ip_address,
                details=details,
                timestamp=datetime.datetime.utcnow()
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)
            return entry
        except Exception as e:
            print(f"Failed to log action: {e}")
            db.rollback()
            return None
