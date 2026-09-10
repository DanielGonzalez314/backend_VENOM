import json
from .base import BaseDispatcher

class EmailDispatcher(BaseDispatcher):
    def can_handle(self, function_name: str) -> bool:
        return function_name == "send_email"
    
    async def execute(self, tool_call, arguments: dict, company_id: str) -> dict:
        from app.services.email_service import EmailService
        
        try:
            to = arguments.get("to", "").strip()
            subject = arguments.get("subject", "").strip()
            body = arguments.get("body", "").strip()
            if not to or not subject or not body:
                raise ValueError("Faltan 'to', 'subject' o 'body'")
            result = await EmailService.send_email(to, subject, body)
            output_data = {"success": result["success"], "message": result["message"]}
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