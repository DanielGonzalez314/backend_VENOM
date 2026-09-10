# app/services/translation_service.py
import logging
import os
from typing import Optional
from google import genai

logger = logging.getLogger("TranslationService")

class TranslationService:
    """Traducción de texto usando Gemini (misma API key que visión)"""
    
    @staticmethod
    async def translate(text: str, target_lang: str, source_lang: str = "auto") -> str:
        """
        Traduce un texto al idioma destino.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Error: GEMINI_API_KEY no configurada"
        
        try:
            # Usar el cliente asíncrono (la nueva librería es asíncrona por defecto)
            client = genai.Client(api_key=api_key)
            
            prompt = f"Traduce el siguiente texto al {target_lang}. "
            if source_lang != "auto":
                prompt += f"El idioma original es {source_lang}. "
            prompt += f"Devuelve solo la traducción, sin comentarios adicionales.\n\nTexto: {text}"
            
            # Usar modelo estable y gratuito (gemini-2.0-flash-exp o gemini-1.5-flash-002)
            response = await client.aio.models.generate_content(
                model="gemini-2.0-flash-exp",  # Modelo actualmente disponible
                contents=prompt,
                config={
                    "temperature": 0.3,
                    "max_output_tokens": 500
                }
            )
            
            translated = response.text.strip()
            logger.info(f"✅ Texto traducido al {target_lang}")
            return translated
            
        except Exception as e:
            logger.error(f"Error en traducción: {e}")
            return f"Error al traducir: {str(e)}"
    
    @staticmethod
    async def detect_language(text: str) -> Optional[str]:
        """Detecta el idioma del texto usando Gemini"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            client = genai.Client(api_key=api_key)
            response = await client.aio.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=f"Responde solo con el nombre del idioma (en español) de este texto: {text}",
                config={"temperature": 0, "max_output_tokens": 20}
            )
            return response.text.strip().lower()
        except Exception as e:
            logger.error(f"Error detectando idioma: {e}")
            return None