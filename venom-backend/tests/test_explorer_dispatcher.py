import pytest
from app.services.dispatchers import VenomDispatcher

@pytest.mark.asyncio
async def test_explorer_open_dispatcher():
    dispatcher = VenomDispatcher()
    # Simular un tool_call
    mock_tool_call = type('obj', (object,), {
        'id': 'call_123',
        'function': type('obj', (object,), {'name': 'explorer_open', 'arguments': '{"path": "Documents"}'})
    })()
    results = await dispatcher.execute_tools([mock_tool_call], "company_xyz")
    assert len(results) == 1
    assert results[0]["name"] == "explorer_open"