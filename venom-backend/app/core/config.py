from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    
    groq_api_key: str
    secret_key: str
    
    # Opcionales con default
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = "sqlite:///./venom.db"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore" # Ignora variables extra en el .env
    )

settings = Settings()