import json
from .base import BaseDispatcher
from app.services.mcp_client import execute_mcp_tool

class LegacyMcpDispatcher(BaseDispatcher):
    def can_handle(self, function_name: str) -> bool:
        return function_name == "mcp_control"
    
    async def execute(self, tool_call, arguments: dict, company_id: str) -> dict:
        server_type = arguments.get("server_type", "").strip()
        tool_name = arguments.get("tool_name", "").strip()
        tool_arguments = arguments.get("arguments", {})
        if not server_type or not tool_name:
            return {
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "output": json.dumps({"success": False, "message": "Faltan 'server_type' o 'tool_name'"})
            }
        tool_arguments["company_id"] = company_id
        try:
            result_text = await execute_mcp_tool(tool_name, tool_arguments, server_type)
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
                "output": json.dumps({"success": False, "message": f"Error MCP: {str(e)}"})
            }