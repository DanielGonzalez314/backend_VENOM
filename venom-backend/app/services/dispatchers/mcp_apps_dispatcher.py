import json
from .base import BaseDispatcher
from app.services.mcp_client import execute_mcp_tool

class McpAppsDispatcher(BaseDispatcher):
    def can_handle(self, function_name: str) -> bool:
        return function_name == "mcp_apps"
    
    async def execute(self, tool_call, arguments: dict, company_id: str) -> dict:
        action = arguments.get("action")
        app_name = arguments.get("app_name", "")
        if not action or not app_name:
            return {
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "output": json.dumps({"success": False, "message": "Faltan 'action' o 'app_name'"})
            }
        tool_args = {"action": action, "app_name": app_name, "company_id": company_id}
        try:
            result_text = await execute_mcp_tool("control_app", tool_args, "apps")
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