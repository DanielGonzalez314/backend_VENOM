import json
from .base import BaseDispatcher
from app.services.mcp_client import execute_mcp_tool

class McpSystemDispatcher(BaseDispatcher):
    def can_handle(self, function_name: str) -> bool:
        return function_name == "mcp_system"
    
    async def execute(self, tool_call, arguments: dict, company_id: str) -> dict:
        action = arguments.get("action")
        if not action:
            return {
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "output": json.dumps({"success": False, "message": "Falta 'action'"})
            }
        tool_args = {"company_id": company_id}
        try:
            if action == "stats":
                result_text = await execute_mcp_tool("get_stats", tool_args, "system")
            elif action == "processes":
                result_text = await execute_mcp_tool("list_processes", tool_args, "system")
            else:
                raise ValueError(f"Acción '{action}' no soportada")
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