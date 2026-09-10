import json
from .base import BaseDispatcher

class WebSearchDispatcher(BaseDispatcher):
    def can_handle(self, function_name: str) -> bool:
        return function_name == "web_search"
    
    async def execute(self, tool_call, arguments: dict, company_id: str) -> dict:
        from app.services.web_search_service import WebSearchService
        
        try:
            query = arguments.get("query", "").strip()
            if not query:
                raise ValueError("Falta el parámetro 'query'")
            result = await WebSearchService.search(query, max_results=5)
            if result.get("success"):
                output_data = {"success": True, "data": result["results"]}
            else:
                output_data = {"success": False, "message": result.get("error", "Error desconocido")}
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