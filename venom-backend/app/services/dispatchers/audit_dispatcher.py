import json
from .base import BaseDispatcher

class AuditDispatcher(BaseDispatcher):
    def can_handle(self, function_name: str) -> bool:
        return function_name == "audit_conversation"
    
    async def execute(self, tool_call, arguments: dict, company_id: str) -> dict:
        from app.services.audit_service import AuditService
        
        try:
            messages_arg = arguments.get("messages", [])
            if not messages_arg or not isinstance(messages_arg, list):
                raise ValueError("Se requiere la lista de mensajes en el campo 'messages'")
            result = await AuditService.audit_conversation(messages_arg)
            return {
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "output": json.dumps(result, ensure_ascii=False)
            }
        except Exception as e:
            return {
                "tool_call_id": tool_call.id,
                "name": tool_call.function.name,
                "output": json.dumps({"success": False, "message": str(e)})
            }