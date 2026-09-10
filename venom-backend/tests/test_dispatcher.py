import pytest
from app.services.dispatcher import VenomDispatcher

class MockToolCall:
    def __init__(self, name, args_json):
        self.id = "call_1"
        self.function = type('obj', (object,), {'name': name, 'arguments': args_json})()

@pytest.mark.asyncio
async def test_generate_pdf_tool():
    tool_call = MockToolCall("generate_report_pdf", '{"title": "Prueba", "content": "Contenido"}')
    results = await VenomDispatcher.execute_tools([tool_call], "test_co")
    assert results[0]["name"] == "generate_report_pdf"
    output = results[0]["output"]
    assert "PDF generado" in output or "error" not in output.lower()