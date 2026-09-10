# app/services/dispatchers/__init__.py
from .base import BaseDispatcher
from .pdf_dispatcher import PdfDispatcher
from .web_search_dispatcher import WebSearchDispatcher
from .email_dispatcher import EmailDispatcher
from .process_file_dispatcher import ProcessFileDispatcher
from .chart_dispatcher import ChartDispatcher
from .compare_documents_dispatcher import CompareDocumentsDispatcher
from .audit_dispatcher import AuditDispatcher
from .list_documents_dispatcher import ListDocumentsDispatcher
from .explorer_dispatcher import ExplorerDispatcher
from .mcp_music_dispatcher import McpMusicDispatcher
from .mcp_apps_dispatcher import McpAppsDispatcher
from .mcp_system_dispatcher import McpSystemDispatcher
from .mcp_windows_dispatcher import McpWindowsDispatcher
from .legacy_dispatcher import LegacyMcpDispatcher

class VenomDispatcher:
    def __init__(self):
        self.handlers = [
            PdfDispatcher(),
            WebSearchDispatcher(),
            EmailDispatcher(),
            ProcessFileDispatcher(),
            ChartDispatcher(),
            CompareDocumentsDispatcher(),
            AuditDispatcher(),
            ListDocumentsDispatcher(),
            ExplorerDispatcher(),
            McpMusicDispatcher(),
            McpAppsDispatcher(),
            McpSystemDispatcher(),
            McpWindowsDispatcher(),
            LegacyMcpDispatcher(),
        ]
    
    async def execute_tools(self, tool_calls, company_id: str):
        import json
        results = []
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except:
                arguments = {}
            handled = False
            for handler in self.handlers:
                if handler.can_handle(function_name):
                    result = await handler.execute(tool_call, arguments, company_id)
                    results.append(result)
                    handled = True
                    break
            if not handled:
                results.append({
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "output": json.dumps({"success": False, "message": f"Herramienta '{function_name}' no implementada"})
                })
        return results