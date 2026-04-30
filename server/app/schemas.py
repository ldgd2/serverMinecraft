from pydantic import BaseModel
from datetime import datetime

class ServerCreate(BaseModel):
    name: str
    version: str
    ram_mb: int
    port: int
    online_mode: bool = False

class ServerResponse(ServerCreate):
    id: int
    status: str
    created_at: datetime
    
    class Config:
        orm_mode = True

class ServerStats(BaseModel):
    status: str
    cpu: float
    ram: float

class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    username: str
    password: str

class ModSearchConnect(BaseModel):
    query: str
    version: str

class RegisterRequest(BaseModel):
    username: str
    password: str
