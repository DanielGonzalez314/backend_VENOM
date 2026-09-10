# app/services/vision_service.py
import base64
import logging
import os
import io
from typing import Optional
import httpx
from PIL import Image

logger = logging.getLogger("VisionService")

class VisionService:
    """
    Servicio especializado en análisis de imágenes para VENOM.
    Como Groq no soporta visión, usamos Hugging Face Inference API (gratuito)
    con modelo BLIP para captioning. Fallback a metadatos si no hay API key.
    """
    
    # Modelo gratuito de Hugging Face para descripción de imágenes
    HF_MODEL = "Salesforce/blip-image-captioning-base"
    HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    
    @classmethod
    async def analyze_image(cls, image_bytes: bytes, user_query: str = "") -> str:
        """
        Analiza una imagen y devuelve una descripción textual.
        
        Args:
            image_bytes: bytes de la imagen (JPEG, PNG, etc.)
            user_query: Consulta del usuario para enfocar el análisis
            
        Returns:
            str: Descripción de la imagen o metadatos
        """
        try:
            # Intentar con Hugging Face
            hf_key = os.getenv("HUGGINGFACE_API_KEY")
            if hf_key:
                description = await cls._analyze_with_huggingface(image_bytes, hf_key)
                if description:
                    return cls._format_response(description, user_query)
            
            # Fallback: metadatos de la imagen
            return cls._extract_metadata(image_bytes, user_query)
            
        except Exception as e:
            logger.error(f"Error en análisis de imagen: {e}")
            return f"⚠️ No se pudo analizar la imagen: {str(e)}"
    
    @classmethod
    async def _analyze_with_huggingface(cls, image_bytes: bytes, api_key: str) -> Optional[str]:
        """Usa Hugging Face Inference API para generar caption de la imagen"""
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    cls.HF_API_URL,
                    headers=headers,
                    content=image_bytes  # Envío directo de bytes
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # El modelo devuelve [{"generated_text": "..."}]
                    if isinstance(result, list) and len(result) > 0:
                        caption = result[0].get("generated_text", "")
                        logger.info(f"✅ Visión HF exitosa: {caption[:50]}...")
                        return caption
                    elif isinstance(result, dict) and "generated_text" in result:
                        return result["generated_text"]
                else:
                    logger.warning(f"HF API error {response.status_code}")
                    return None
                    
        except httpx.TimeoutException:
            logger.warning("Timeout en Hugging Face")
            return None
        except Exception as e:
            logger.warning(f"Error en HF: {e}")
            return None
    
    @classmethod
    def _extract_metadata(cls, image_bytes: bytes, user_query: str) -> str:
        """Extrae metadatos básicos como fallback"""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            format_img = img.format or "desconocido"
            mode = img.mode
            
            return f"""
[METADATOS DE LA IMAGEN]
- Formato: {format_img}
- Dimensiones: {width} x {height} px
- Modo de color: {mode}
- Peso: {len(image_bytes)} bytes

[CONTEXTO]
Usuario preguntó: "{user_query}"

⚠️ NOTA: Groq no tiene capacidades de visión. Para analizar el contenido visual, configura HUGGINGFACE_API_KEY en .env (gratis en huggingface.co/settings/tokens).
""".strip()
        except Exception as e:
            return f"Error al leer imagen: {str(e)}"
    
    @classmethod
    def _format_response(cls, description: str, user_query: str) -> str:
        """Formatea la respuesta según la consulta del usuario"""
        if user_query:
            return f"🔍 Análisis visual para: '{user_query}'\n📷 Descripción: {description}"
        return f"📷 Descripción de la imagen: {description}"
    
    @classmethod
    async def is_image(cls, file_bytes: bytes) -> bool:
        """Detecta si los bytes corresponden a una imagen válida"""
        # Firmas mágicas comunes
        signatures = [
            (b'\x89PNG\r\n\x1a\n', 'png'),
            (b'\xff\xd8\xff', 'jpg'),
            (b'GIF87a', 'gif'),
            (b'GIF89a', 'gif'),
            (b'RIFF', 'webp'),
        ]
        for sig, _ in signatures:
            if file_bytes.startswith(sig):
                return True
        # Verificar con PIL
        try:
            Image.open(io.BytesIO(file_bytes))
            return True
        except:
            return False