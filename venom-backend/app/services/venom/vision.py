import io
import logging
from app.services.vision_service import VisionService

logger = logging.getLogger("VenomEngine")

async def analyze_visual_data(image_bytes: bytes, user_query: str, groq_client=None) -> str:
    """Analiza una imagen usando VisionService."""
    try:
        return await VisionService.analyze_image(image_bytes, user_query, groq_client=groq_client)
    except Exception as e:
        logger.error(f"❌ Error en VisionService: {e}", exc_info=True)
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(image_bytes))
            return f"""
[ANÁLISIS LOCAL DE IMAGEN]
No se pudo usar el servicio de visión avanzada.
Metadatos:
- Formato: {img.format}
- Dimensiones: {img.width} x {img.height}
- Modo: {img.mode}
- Peso: {len(image_bytes)} bytes
Consulta: {user_query}
"""
        except:
            return f"No se pudo analizar la imagen. Consulta: {user_query}"