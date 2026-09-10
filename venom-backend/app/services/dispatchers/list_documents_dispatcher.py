import json
import os
from .base import BaseDispatcher

class ListDocumentsDispatcher(BaseDispatcher):
    def can_handle(self, function_name: str) -> bool:
        return function_name == "list_documents"
    
    async def execute(self, tool_call, arguments: dict, company_id: str) -> dict:
        try:
            upload_dir = "static/uploads"
            documents = []
            if os.path.exists(upload_dir):
                for filename in os.listdir(upload_dir):
                    parts = filename.split('_', 1)
                    if len(parts) == 2:
                        doc_id = parts[0]
                        doc_name = parts[1]
                        documents.append({"id": doc_id, "filename": doc_name})
            output_data = {"success": True, "documents": documents, "count": len(documents)}
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