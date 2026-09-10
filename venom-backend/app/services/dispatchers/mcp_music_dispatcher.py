import json
from .base import BaseDispatcher
from app.services.mcp_client import execute_mcp_tool

class McpMusicDispatcher(BaseDispatcher):
    def can_handle(self, function_name: str) -> bool:
        return function_name == "mcp_music"
    
    async def execute(self, tool_call, arguments: dict, company_id: str) -> dict:
        action = arguments.get("action")
        query = arguments.get("query", "")
        if not action:
            return {
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "output": json.dumps({"success": False, "message": "Falta 'action'"})
            }
        tool_args = {"action": action, "query": query, "company_id": company_id}
        try:
            result_text = await execute_mcp_tool(action, tool_args, "music")
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