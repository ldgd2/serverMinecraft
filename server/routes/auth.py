from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models.user import User
from app.controllers.auth_controller import AuthController
from database.schemas import Token, UserLogin
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
from app.services.auth_service import verify_password, create_access_token, get_password_hash
from app.services.audit_service import AuditService
from core.responses import APIResponse
from app.services.auth_suspend_manager import challenge_manager

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

router = APIRouter(prefix="/auth", tags=["Auth"])
auth_controller = AuthController()

class RegisterRequest(BaseModel):
    username: str
    password: str

from app.services.auth_service import get_current_user as verify_token_service
from fastapi.security import HTTPAuthorizationCredentials
import re

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")
    print(f"DEBUG: get_current_user called. auth_header={auth_header}")
    if auth_header:
        match = re.match(r"^Bearer\s+(.+)$", auth_header, re.IGNORECASE)
        if match:
            token = match.group(1)
            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
            try:
                # Usar la función de verificación oficial para máxima compatibilidad
                user = verify_token_service(credentials=credentials, db=db)
                if user:
                    return user
            except Exception as e:
                print(f"DEBUG: Token verification failed: {e}")
                pass # Fallback to challenge

    # No valid token found -> Challenge HTTP stateless
    ip = request.client.host
    print(f"DEBUG: Unauthenticated request from {ip}. Issuing challenge...")
    
    # 1. Crear Desafío
    challenge = challenge_manager.create_challenge(ip)
    
    # 2. Requerir Autenticación (401 con JSON Body)
    # Detail como DICT para que FastAPI lo serialice a JSON automáticamente
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "status": "auth_required",
            "challenge_id": challenge["challenge_id"],
            "pub_key": challenge["pub_key"]
        },
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.post("/login", response_model=APIResponse[Token])
def login(user_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    print(f"DEBUG: Login endpoint hit. Username: {repr(user_data.username)}")
    token = auth_controller.login(db, user_data.username, user_data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = auth_controller.get_user_by_username(db, user_data.username)
    if user:
        AuditService.log_action(db, user, "LOGIN", request.client.host, "User logged in")
    return APIResponse(status="success", message="Login successful", data=Token(access_token=token, token_type="bearer"))

@router.post("/register")
def register(user_data: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    if auth_controller.get_user_by_username(db, user_data.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed = get_password_hash(user_data.password)
    user = User(username=user_data.username, hashed_password=hashed)
    db.add(user)
    db.commit()
    
    AuditService.log_action(db, user, "REGISTER", request.client.host, f"Registered user {user.username}")
    return APIResponse(status="success", message="User created successfully", data=None)

class AuthResponse(BaseModel):
    challenge_id: str
    password_encrypted: str
    username: str

@router.post("/respond")
def respond_auth(data: AuthResponse, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host
    print(f"DEBUG: Auth Response received from {ip} for {data.username}")
    try:
        # 1. Validar desafío existe y pertenece a la IP
        if not challenge_manager.validate_challenge(data.challenge_id, ip):
             raise HTTPException(status_code=400, detail="Desafío inválido o expirado")

        # 2. Descifrar
        password = challenge_manager.decrypt_password(data.challenge_id, data.password_encrypted)
        
        # 3. Validar Credenciales
        token = auth_controller.login(db, data.username, password)
        if not token:
             raise HTTPException(status_code=401, detail="Incorrect credentials")
             
        # 4. Devolver Token para que el cliente reintente
        return APIResponse(
             status="success", 
             message="Authenticated", 
             data=Token(access_token=token, token_type="bearer")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
