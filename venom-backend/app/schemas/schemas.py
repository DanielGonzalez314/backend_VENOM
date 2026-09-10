from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

# --- 1. AUTENTICACIÓN Y REGISTRO ---

class UserCreate(BaseModel):
    """Esquema para el registro de nuevos usuarios (POST /api/register)"""
    full_name: str = Field(..., min_length=1, example="John Doe")
    email: EmailStr
    password: str = Field(..., min_length=6, example="password123")
    company_name: Optional[str] = "Nueva Empresa"

class UserResponse(BaseModel):
    """Respuesta de datos de usuario (Sin password)"""
    full_name: str
    email: EmailStr
    company_id: str
    company_name: Optional[str] = None # Agregado para el Sidebar del frontend
    is_active: bool = True

    class Config:
        from_attributes = True

class Token(BaseModel):
    """Formato del JWT devuelto tras el login"""
    access_token: str
    refresh_token: Optional[str] = None # Agregado para que client.js funcione
    token_type: str
    user: Optional[UserResponse] = None

# --- 2. GESTIÓN DE EMPRESA ---

class CompanyResponse(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- 3. DATA LAKE (CONOCIMIENTO CORPORATIVO) ---

class DocumentResponse(BaseModel):
    """Esquema para listar archivos en el Knowledge Base"""
    id: str
    filename: str
    file_type: Optional[str] = None
    file_size: Optional[int] = 0 # Agregado para KnowledgeBase.jsx
    uploaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- 4. VENOM ENGINE (CHAT Y MENSAJERÍA) ---

class MessageResponse(BaseModel):
    """Esquema para mensajes individuales dentro de un chat"""
    role: str
    content: str
    # FIX CRÍTICO: Optional para evitar el Error 500 si la DB no tiene la fecha
    created_at: Optional[datetime] = None 

    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    """Esquema para el Sidebar y detalle de chat"""
    id: str
    title: Optional[str] = "Nueva Conversación"
    created_at: Optional[datetime] = None
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    """Payload para consultas simples de texto"""
    query: str