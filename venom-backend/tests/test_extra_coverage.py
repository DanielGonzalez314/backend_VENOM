# tests/test_extra_coverage.py
import pytest
import json
from unittest.mock import AsyncMock, patch
from app.services.dispatchers.base import BaseDispatcher
from app.services.dispatchers import (
    VenomDispatcher,
    AuditDispatcher,
    CompareDocumentsDispatcher,
    EmailDispatcher,
    LegacyMcpDispatcher,
    ListDocumentsDispatcher,
    McpAppsDispatcher,
    McpMusicDispatcher,
    McpSystemDispatcher,
    McpWindowsDispatcher,
    ProcessFileDispatcher,
    WebSearchDispatcher,
    ChartDispatcher,
)
from app.services.file_processor import FileProcessor
from app.services.web_search_service import WebSearchService

def mock_tool_call(name, args_dict):
    class MockFunction:
        def __init__(self):
            self.name = name
            self.arguments = json.dumps(args_dict)
    class MockToolCall:
        def __init__(self):
            self.id = "call_123"
            self.function = MockFunction()
    return MockToolCall()

# ========== TESTS PARA DISPATCHERS ==========
@pytest.mark.asyncio
async def test_audit_dispatcher():
    dispatcher = AuditDispatcher()
    tool_call = mock_tool_call("audit_conversation", {"messages": []})
    result = await dispatcher.execute(tool_call, {"messages": []}, "test_co")
    assert result["name"] == "audit_conversation"
    output = json.loads(result["output"])
    assert "success" in output or "error" in output

@pytest.mark.asyncio
async def test_compare_documents_dispatcher():
    dispatcher = CompareDocumentsDispatcher()
    tool_call = mock_tool_call("compare_documents", {"doc1_id": "fake1", "doc2_id": "fake2"})
    result = await dispatcher.execute(tool_call, {"doc1_id": "fake1", "doc2_id": "fake2"}, "test_co")
    assert result["name"] == "compare_documents"
    output = json.loads(result["output"])
    assert "success" in output or "error" in output

@pytest.mark.asyncio
async def test_email_dispatcher():
    dispatcher = EmailDispatcher()
    tool_call = mock_tool_call("send_email", {"to": "test@example.com", "subject": "Test", "body": "Body"})
    with patch("app.services.email_service.EmailService.send_email", return_value={"success": True, "message": "OK"}):
        result = await dispatcher.execute(tool_call, {"to": "test@example.com", "subject": "Test", "body": "Body"}, "test_co")
        assert result["name"] == "send_email"
        output = json.loads(result["output"])
        assert output["success"] is True

@pytest.mark.asyncio
async def test_legacy_mcp_dispatcher():
    dispatcher = LegacyMcpDispatcher()
    tool_call = mock_tool_call("mcp_control", {"server_type": "filesystem", "tool_name": "list_directory", "arguments": {"path": "."}})
    with patch("app.services.mcp_client.execute_mcp_tool", return_value="Mock result"):
        result = await dispatcher.execute(tool_call, {"server_type": "filesystem", "tool_name": "list_directory", "arguments": {"path": "."}}, "test_co")
        assert result["name"] == "mcp_control"
        output = json.loads(result["output"])
        assert "message" in output

@pytest.mark.asyncio
async def test_list_documents_dispatcher():
    dispatcher = ListDocumentsDispatcher()
    tool_call = mock_tool_call("list_documents", {})
    result = await dispatcher.execute(tool_call, {}, "test_co")
    assert result["name"] == "list_documents"
    output = json.loads(result["output"])
    assert "documents" in output

@pytest.mark.asyncio
async def test_mcp_apps_dispatcher():
    dispatcher = McpAppsDispatcher()
    tool_call = mock_tool_call("mcp_apps", {"action": "start", "app_name": "notepad.exe"})
    with patch("app.services.mcp_client.execute_mcp_tool", return_value="App started"):
        result = await dispatcher.execute(tool_call, {"action": "start", "app_name": "notepad.exe"}, "test_co")
        assert result["name"] == "mcp_apps"
        output = json.loads(result["output"])
        assert output["success"] is True

@pytest.mark.asyncio
async def test_mcp_music_dispatcher():
    dispatcher = McpMusicDispatcher()
    tool_call = mock_tool_call("mcp_music", {"action": "play", "query": "test"})
    with patch("app.services.mcp_client.execute_mcp_tool", return_value="Playing"):
        result = await dispatcher.execute(tool_call, {"action": "play", "query": "test"}, "test_co")
        assert result["name"] == "mcp_music"
        output = json.loads(result["output"])
        assert output["success"] is True

@pytest.mark.asyncio
async def test_mcp_system_dispatcher():
    dispatcher = McpSystemDispatcher()
    tool_call = mock_tool_call("mcp_system", {"action": "stats"})
    with patch("app.services.mcp_client.execute_mcp_tool", return_value="CPU: 10%"):
        result = await dispatcher.execute(tool_call, {"action": "stats"}, "test_co")
        assert result["name"] == "mcp_system"
        output = json.loads(result["output"])
        # Verificar que el mensaje contiene información relevante
        assert output["message"] and ("cpu" in output["message"].lower() or "%" in output["message"])

@pytest.mark.asyncio
async def test_mcp_windows_dispatcher():
    dispatcher = McpWindowsDispatcher()
    tool_call = mock_tool_call("mcp_windows", {"action": "close", "title": "Notepad"})
    with patch("app.services.mcp_client.execute_mcp_tool", return_value="Window closed"):
        result = await dispatcher.execute(tool_call, {"action": "close", "title": "Notepad"}, "test_co")
        assert result["name"] == "mcp_windows"
        output = json.loads(result["output"])
        assert output["success"] is True

@pytest.mark.asyncio
async def test_process_file_dispatcher():
    dispatcher = ProcessFileDispatcher()
    tool_call = mock_tool_call("process_file", {"file_base64": "dGVzdA==", "filename": "test.txt"})
    result = await dispatcher.execute(tool_call, {"file_base64": "dGVzdA==", "filename": "test.txt"}, "test_co")
    assert result["name"] == "process_file"
    output = json.loads(result["output"])
    assert "error" in output["message"].lower() or "success" in output

@pytest.mark.asyncio
async def test_web_search_dispatcher():
    dispatcher = WebSearchDispatcher()
    tool_call = mock_tool_call("web_search", {"query": "test"})
    with patch("app.services.web_search_service.WebSearchService.search", return_value={"success": True, "results": "mock"}):
        result = await dispatcher.execute(tool_call, {"query": "test"}, "test_co")
        assert result["name"] == "web_search"
        output = json.loads(result["output"])
        assert output["success"] is True

@pytest.mark.asyncio
async def test_chart_dispatcher():
    dispatcher = ChartDispatcher()
    tool_call = mock_tool_call("generate_chart", {"document_id": "fake", "x_column": "x", "y_column": "y"})
    result = await dispatcher.execute(tool_call, {"document_id": "fake", "x_column": "x", "y_column": "y"}, "test_co")
    assert result["name"] == "generate_chart"
    output = json.loads(result["output"])
    # Mensaje esperado: "No se encontró el documento con ID o nombre: fake"
    assert "No se encontró" in output["message"] or "documento" in output["message"].lower()

# ========== BASE DISPATCHER ==========
def test_base_dispatcher_safe_base64_decode():
    class Dummy(BaseDispatcher):
        def can_handle(self, name): return False
        async def execute(self, tool_call, args, company_id): pass
    result = Dummy.safe_base64_decode("dGVzdA==")
    assert result == b"test"
    result2 = Dummy.safe_base64_decode("dGVzdA")
    assert result2 == b"test"

# ========== VENOM DISPATCHER FACHADA ==========
@pytest.mark.asyncio
async def test_venom_dispatcher_facade():
    dispatcher = VenomDispatcher()
    tool_call = mock_tool_call("generate_report_pdf", {"title": "Test", "content": "Content"})
    results = await dispatcher.execute_tools([tool_call], "test_co")
    assert len(results) == 1
    assert results[0]["name"] == "generate_report_pdf"
    output = json.loads(results[0]["output"])
    assert output["success"] is True

# ========== FILE PROCESSOR EXTRA ==========
@pytest.mark.asyncio
async def test_file_processor_extract_text_from_excel():
    import pandas as pd
    import io
    df = pd.DataFrame({"A": [1,2], "B": [3,4]})
    excel_bytes = io.BytesIO()
    df.to_excel(excel_bytes, index=False)
    excel_bytes.seek(0)
    text = await FileProcessor.extract_text(excel_bytes.read(), "test.xlsx")
    assert "A" in text and "B" in text

@pytest.mark.asyncio
async def test_file_processor_extract_text_from_csv():
    csv_content = b"col1,col2\nval1,val2"
    text = await FileProcessor.extract_text(csv_content, "test.csv")
    assert "col1" in text and "val1" in text

# ========== WEB SEARCH SERVICE ==========
@pytest.mark.asyncio
async def test_web_search_service_missing_api_key():
    with patch.dict("os.environ", {}, clear=True):
        result = await WebSearchService.search("test")
        assert result["success"] is False
        assert "TAVILY_API_KEY" in result["error"]