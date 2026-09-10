import json
from .base import BaseDispatcher
from app.services.mcp_client import execute_mcp_tool

class ExplorerDispatcher(BaseDispatcher):
    # Lista de todas las herramientas relacionadas con el explorador
    HANDLED_FUNCTIONS = [
        "explorer_open", "explorer_list", "explorer_create_folder",
        "explorer_create_file", "explorer_delete", "explorer_move", "explorer_read"
    ]
    
    def can_handle(self, function_name: str) -> bool:
        return function_name in self.HANDLED_FUNCTIONS
    
    async def execute(self, tool_call, arguments: dict, company_id: str) -> dict:
        function_name = tool_call.function.name
        # Mapear función a tool_name de mcp_client y ajustar argumentos
        mapping = {
            "explorer_open": ("open_explorer", {"path": arguments.get("path", "")}),
            "explorer_list": ("list_directory", {"path": arguments.get("path", "")}),
            "explorer_create_folder": ("create_directory", {"path": arguments.get("path", "")}),
            "explorer_create_file": ("create_file", {
                "path": arguments.get("path", ""),
                "content": arguments.get("content", "")
            }),
            "explorer_delete": ("delete", {"path": arguments.get("path", "")}),
            "explorer_move": ("move", {
                "source": arguments.get("source", ""),
                "destination": arguments.get("destination", "")
            }),
            "explorer_read": ("read_file", {"path": arguments.get("path", "")}),
        }
        tool_name, tool_args = mapping[function_name]
        tool_args["company_id"] = company_id
        try:
            result_text = await execute_mcp_tool(tool_name, tool_args, "filesystem")
            output_data = {"success": True, "message": result_text}
            return {
                "tool_call_id": tool_call.id,
                "name": function_name,
                "output": json.dumps(output_data, ensure_ascii=False)
            }
        except Exception as e:
            return {
                "tool_call_id": tool_call.id,
                "name": function_name,
                "output": json.dumps({"success": False, "message": str(e)})
            }