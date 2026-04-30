from sqlalchemy.orm import Session
from database.models.user import User
from app.services.auth_service import verify_password, create_access_token
from fastapi import HTTPException, status

class AuthController:
    def login(self, db: Session, username: str, password: str):
        if not username or not password:
             return None
        
        username = username.strip()
        password = password.strip()
        print(f"DEBUG: Attempting login for user: {repr(username)} with password: {repr(password)}")
        user = db.query(User).filter(User.username == username).first()
        print(f"DEBUG: User found: {user}")
        
        if user:
             print(f"DEBUG: Verify password for user '{user.username}'")
             is_valid = verify_password(password, user.hashed_password)
             print(f"DEBUG: Password valid: {is_valid}")
             if not is_valid:
                 print(f"DEBUG: Password verification failed for user '{username}'")
                 return None
        else:
             print(f"DEBUG: User '{username}' not found in DB")
             return None
             
        access_token = create_access_token(data={"sub": user.username})
        
        # Audit Log
        from app.services.bitacora_service import BitacoraService
        BitacoraService.add_log(
            db=db, 
            username=user.username, 
            action="LOGIN_SUCCESS", 
            ip_address=None,  # Or get from request if possible in future
            details="User logged in successfully via API",
            severity="CRITICAL"
        )
        
        return access_token

    def get_user_by_username(self, db: Session, username: str):
         return db.query(User).filter(User.username == username).first()
