from sqlalchemy.orm import Session
from database.models.bitacora import Bitacora
from database.connection import SessionLocal
import datetime

class BitacoraService:
    @staticmethod
    def add_log(db: Session, username: str, action: str, ip_address: str = None, details: str = None, severity: str = "COMMON"):
        """
        Adds a new entry to the bitacora (audit log).
        """
        try:
            log_entry = Bitacora(
                username=username,
                action=action,
                ip_address=ip_address,
                details=details,
                severity=severity,
                timestamp=datetime.datetime.utcnow()
            )
            db.add(log_entry)
            db.commit()
            db.refresh(log_entry)
            return log_entry
        except Exception as e:
            # Fallback for when we don't want to crash the main flow just because logging failed
            print(f"Failed to create bitacora entry: {e}")
            db.rollback()
            return None

    @staticmethod
    def add_log_background(username: str, action: str, ip_address: str = None, details: str = None):
        """
        Adds a log entry using a new temporary session. 
        Useful for async contexts or where a session isn't readily available.
        """
        db = SessionLocal()
        try:
            BitacoraService.add_log(db, username, action, ip_address, details)
        finally:
            db.close()
