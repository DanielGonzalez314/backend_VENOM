import sys
import json
from loguru import logger
from app.database import SessionLocal
# Importación diferida para evitar ciclos
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class LogEntry(Base):
    __tablename__ = "system_logs"
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(50))
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

def db_sink(message):
    """Función que guarda el log en la base de datos."""
    record = message.record
    db = SessionLocal()
    try:
        log_item = LogEntry(
            level=record["level"].name,
            message=record["message"]
        )
        db.add(log_item)
        db.commit()
    except Exception as e:
        print(f"Error guardando log en DB: {e}")
    finally:
        db.close()

def setup_logging():
    logger.remove()
    
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )

    logger.add(db_sink, level="WARNING") 

    logger.add("logs/events.json", serialize=True, rotation="10MB")