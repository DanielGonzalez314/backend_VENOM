# tests/test_vision_service.py
import pytest
import base64
from unittest.mock import patch
from app.services.vision_service import VisionService

# Imagen válida de 1x1 píxel rojo en formato PNG (base64)
VALID_IMAGE_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
VALID_IMAGE_BYTES = base64.b64decode(VALID_IMAGE_BASE64)


@pytest.mark.asyncio
async def test_analyze_image_returns_metadata_when_no_hf_key():
    """
    Cuando no hay HUGGINGFACE_API_KEY, el servicio debe devolver metadatos
    de la imagen (dimensiones, formato) o un mensaje de error controlado.
    """
    with patch.dict('os.environ', {}, clear=True):
        result = await VisionService.analyze_image(VALID_IMAGE_BYTES, "test")
        # La respuesta debe contener información sobre la imagen
        assert any(phrase in result for phrase in [
            "METADATOS DE LA IMAGEN",
            "Formato: PNG",
            "Dimensiones: 1 x 1",
            "no se pudo analizar"
        ]), f"Respuesta inesperada: {result}"


@pytest.mark.asyncio
async def test_analyze_image_with_invalid_bytes_returns_error():
    """
    Si se pasan bytes que no representan una imagen válida,
    debe devolver un mensaje de error claro.
    """
    with patch.dict('os.environ', {}, clear=True):
        invalid_bytes = b"no soy una imagen"
        result = await VisionService.analyze_image(invalid_bytes, "test")
        assert "Error al leer imagen" in result or "no se pudo analizar" in result


@pytest.mark.asyncio
async def test_is_image_detects_valid_image():
    """Verifica que is_image detecte correctamente una imagen válida."""
    assert await VisionService.is_image(VALID_IMAGE_BYTES) is True


@pytest.mark.asyncio
async def test_is_image_rejects_invalid_data():
    """Verifica que is_image rechace datos que no son imagen."""
    assert await VisionService.is_image(b"texto plano") is False