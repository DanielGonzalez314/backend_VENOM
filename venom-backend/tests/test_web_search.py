import pytest
from unittest.mock import patch, AsyncMock
from app.services.web_search_service import WebSearchService

@pytest.mark.asyncio
async def test_search_missing_api_key():
    with patch.dict('os.environ', {}, clear=True):
        result = await WebSearchService.search("test")
        assert result["success"] is False
        assert "TAVILY_API_KEY" in result["error"]