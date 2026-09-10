import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, Text, DateTime, Integer, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

# Función auxiliar para generar IDs únicos de tipo string
def generate_uuid():
    return str(uuid.uuid4())

class Company(Base):
    __tablename__ = "companies"
    # Usamos default=generate_uuid para que SQLAlchemy asigne el ID automáticamente
    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    name = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="company", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"
    # El email es PK, asegúrate de que siempre sea único
    email = Column(String, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    company_id = Column(String, ForeignKey("companies.id"))
    
    company = relationship("Company", back_populates="users")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    file_type = Column(String) 
    file_size = Column(Integer) 
    company_id = Column(String, ForeignKey("companies.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    company = relationship("Company", back_populates="documents")

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    title = Column(String, default="Nueva Sesión")
    user_email = Column(String, ForeignKey("users.email"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String) 
    content = Column(Text)
    metadata_json = Column(JSON, nullable=True) 
    # CAMBIO: Nombre unificado para que coincida con esquemas y endpoints
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")

class SemanticCache(Base):
    __tablename__ = "semantic_cache"
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String, ForeignKey("companies.id"))
    query_hash = Column(String, index=True) 
    query_text = Column(Text)
    answer_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String, unique=True, index=True)
    user_email = Column(String, ForeignKey("users.email"))
    expires_at = Column(DateTime)
    
    user = relationship("User", back_populates="refresh_tokens")