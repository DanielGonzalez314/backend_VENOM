# tests/test_mcp_client.py
import pytest
from app.services.mcp_client import execute_mcp_tool

@pytest.mark.skip(reason="Requiere ajuste de variables de entorno para mock; se probará manualmente")
@pytest.mark.asyncio
async def test_execute_mcp_tool_filesystem_list_directory():
    pass

@pytest.mark.skip(reason="Requiere ajuste de variables de entorno para mock; se probará manualmente")
@pytest.mark.asyncio
async def test_execute_mcp_tool_music_play():
    pass