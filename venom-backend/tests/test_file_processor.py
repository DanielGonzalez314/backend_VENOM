import pytest
from app.services.file_processor import FileProcessor

@pytest.mark.asyncio
async def test_extract_text_from_txt():
    content = b"Hola mundo"
    text = await FileProcessor.extract_text(content, "test.txt")
    assert "Hola mundo" in text

@pytest.mark.asyncio
async def test_get_metadata_from_txt():
    content = b"contenido"
    meta = await FileProcessor.get_metadata(content, "sample.txt")
    assert meta["extension"] == "txt"
    assert meta["size_bytes"] == len(content)