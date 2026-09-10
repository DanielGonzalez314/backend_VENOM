import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from groq import AsyncGroq
from dotenv import load_dotenv
from pydantic import BaseModel
from loguru import logger

# Importaciones locales
from app.database import get_db
from app.models import models
from app.schemas import schemas
from app.core import security
from app.services.venom_engine import VenomEngine

load_dotenv()
router = APIRouter()
groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

# Esquema para el Refresh Token
class RefreshRequest(BaseModel):
    refresh_token: str

# --- 0. AUTENTICACIÓN (Sin cambios, funciona OK) ---

@router.post("/register", response_model=schemas.UserResponse)
async def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    user_exists = db.query(models.User).filter(models.User.email == user_in.email).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="El email ya está registrado.")
    try:
        company_name = getattr(user_in, 'company_name', f"Corporación {user_in.full_name}")
        new_company = models.Company(name=company_name)
        db.add(new_company)
        db.flush() 
        hashed_pw = security.get_password_hash(user_in.password)
        new_user = models.User(
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_pw,
            company_id=new_company.id,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en registro: {str(e)}")

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    access_token = security.create_access_token(data={"sub": user.email})
    refresh_token = security.create_refresh_token(email=user.email) 
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "email": user.email,
            "full_name": user.full_name,
            "company_id": str(user.company_id),
            "company_name": user.company.name if user.company else "Corporación Venom"
        }
    }

# --- 1. KNOWLEDGE BASE (INGESTA Y DOCUMENTOS) ---

@router.post("/ingest/file")
async def ingest_file(
    file: UploadFile = File(...),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        file_bytes = await file.read()
        # Generamos el UUID como string para cumplir con el modelo
        doc_id = str(uuid.uuid4())
        
        # 1. Indexar en ChromaDB (RAG)
        await VenomEngine.process_and_index(
            file_bytes=file_bytes,
            filename=file.filename,
            doc_id=doc_id,
            company_id=str(current_user.company_id)
        )
        
        # 2. Guardar en PostgreSQL usando los nombres exactos de models.py
        new_doc = models.Document(
            id=doc_id,
            filename=file.filename,
            company_id=current_user.company_id,
            file_type=file.filename.split('.')[-1] if '.' in file.filename else 'file',
            file_size=len(file_bytes) # Añadido para completar el modelo
        )
        db.add(new_doc)
        db.commit()
        
        return {"status": "success", "filename": file.filename, "doc_id": doc_id}
    except Exception as e:
        db.rollback()
        logger.error(f"Error Ingest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents", response_model=List[schemas.DocumentResponse])
async def list_documents(
    current_user: models.User = Depends(security.get_current_user), 
    db: Session = Depends(get_db)
):
    # CORRECCIÓN: Usamos uploaded_at porque created_at no existe en el modelo Document
    return db.query(models.Document).filter(
        models.Document.company_id == current_user.company_id
    ).order_by(models.Document.uploaded_at.desc()).all()

@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str, 
    current_user: models.User = Depends(security.get_current_user), 
    db: Session = Depends(get_db)
):
    doc = db.query(models.Document).filter(
        models.Document.id == doc_id,
        models.Document.company_id == current_user.company_id
    ).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    try:
        await VenomEngine.purge_document(doc_id=doc_id, company_id=str(current_user.company_id))
        db.delete(doc)
        db.commit()
        return {"message": "Purgado con éxito", "status": "deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- 2. CONVERSACIONES ---

@router.get("/conversations", response_model=List[schemas.ConversationResponse])
async def get_all_conversations(
    current_user: models.User = Depends(security.get_current_user), 
    db: Session = Depends(get_db)
):
    return db.query(models.Conversation).filter(
        models.Conversation.user_email == current_user.email
    ).order_by(models.Conversation.created_at.desc()).all()

@router.get("/conversations/{conversation_id}", response_model=schemas.ConversationResponse)
async def get_conversation_detail(
    conversation_id: str, 
    current_user: models.User = Depends(security.get_current_user), 
    db: Session = Depends(get_db)
):
    conv = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id, 
        models.Conversation.user_email == current_user.email
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return conv

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str, 
    current_user: models.User = Depends(security.get_current_user), 
    db: Session = Depends(get_db)
):
    conv = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id, 
        models.Conversation.user_email == current_user.email
    ).first()
    
    if not conv:
        raise HTTPException(status_code=404, detail="No existe la conversación")
    
    try:
        # Tu lógica original de borrado manual de mensajes
        db.query(models.Message).filter(models.Message.conversation_id == conversation_id).delete()
        db.delete(conv)
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- 3. CHAT (IA) ---

@router.post("/ask/{conversation_id}")
async def chat_multimodal(
    conversation_id: str,
    query: str = Form(...),
    file: Optional[UploadFile] = File(None),
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Identificar si es una conversación nueva o existente
    valid_new_ids = ["new", "default_conv", "undefined", "null", ""]
    is_new = conversation_id in valid_new_ids
    actual_id = f"conv_{uuid.uuid4().hex[:8]}" if is_new else conversation_id

    # 2. Asegurar existencia de la conversación en PostgreSQL
    conv = db.query(models.Conversation).filter(models.Conversation.id == actual_id).first()
    if not conv:
        short_title = query[:40] if query else "Nueva Consulta"
        conv = models.Conversation(id=actual_id, user_email=current_user.email, title=short_title)
        db.add(conv)
        db.commit()

    file_bytes = await file.read() if file else None

    # 3. Obtener historial previo
    history_db = db.query(models.Message).filter(
        models.Message.conversation_id == actual_id
    ).order_by(models.Message.created_at.asc()).all()

    try:
        # 4. Llamada al motor Venom
        # Forzamos user_name a string para evitar el error 'name'
        user_name_str = str(current_user.full_name) if current_user.full_name else "Usuario"
        
        answer = await VenomEngine.generate_venom_response(
            query=query, 
            user_name=user_name_str,
            company_id=str(current_user.company_id), 
            groq_client=groq_client,
            db_session=db, 
            file_bytes=file_bytes, 
            history_db=history_db
        )

        # 5. Guardar la interacción en la DB
        db.add(models.Message(conversation_id=actual_id, role="user", content=query))
        db.add(models.Message(conversation_id=actual_id, role="assistant", content=answer))
        db.commit()

        return {
            "conversation_id": actual_id, 
            "answer": answer, 
            "title": conv.title, 
            "is_new": is_new
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Fallo en VenomEngine: {str(e)}")
        
        # 6. Plan de Rescate: Si el motor falla (por el PDF o Logs), respondemos igual
        # Esto evita el Error 500 y el bloqueo de CORS en el navegador
        error_msg = "He recibido tu mensaje, pero tuve un problema técnico con mis herramientas. ¿Podemos intentarlo de nuevo?"
        return {
            "conversation_id": actual_id,
            "answer": error_msg,
            "title": conv.title,
            "is_new": is_new,
            "error_log": str(e)
        }