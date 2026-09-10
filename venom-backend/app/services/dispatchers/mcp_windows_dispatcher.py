import json
from .base import BaseDispatcher
from app.services.mcp_client import execute_mcp_tool

class McpWindowsDispatcher(BaseDispatcher):
    def can_handle(self, function_name: str) -> bool:
        return function_name == "mcp_windows"
    
    async def execute(self, tool_call, arguments: dict, company_id: str) -> dict:
        action = arguments.get("action")
        title = arguments.get("title", "")
        if not action or not title:
            return {
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "output": json.dumps({"success": False, "message": "Faltan 'action' o 'title'"})
            }
        tool_args = {"action": action, "title": title, "company_id": company_id}
        try:
            result_text = await execute_mcp_tool("control_window", tool_args, "windows")
            output_data = {"success": True, "message": result_text}
            return {
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "output": json.dumps(output_data, ensure_ascii=False)
            }
        except Exception as e:
            return {
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "output": json.dumps({"success": False, "message": str(e)})
            }