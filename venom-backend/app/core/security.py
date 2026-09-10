from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database import get_db
from app.models import models

# Configuración de hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# El tokenUrl debe apuntar a la ruta exacta donde está el login.
# Al tener prefix="/api" en main.py, "api/login" es lo correcto.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

# --- FUNCIONES DE CONTRASEÑA ---

def get_password_hash(password: str) -> str:
    """Hash para registro de usuarios"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificación para login"""
    return pwd_context.verify(plain_password, hashed_password)

# --- GESTIÓN DE TOKENS ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def create_refresh_token(email: str):
    """Genera un token de larga duración (7 días) para renovar sesión"""
    expires_delta = timedelta(days=7)
    return create_access_token(
        data={"sub": email, "type": "refresh"}, 
        expires_delta=expires_delta
    )

# --- DEPENDENCIA DE USUARIO ACTUAL ---

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el acceso",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        
        # Bloqueamos el uso de refresh tokens para peticiones normales
        if email is None or payload.get("type") == "refresh":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
        
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
        
    return user