import json
import os
from .base import BaseDispatcher

class CompareDocumentsDispatcher(BaseDispatcher):
    def can_handle(self, function_name: str) -> bool:
        return function_name == "compare_documents"
    
    async def execute(self, tool_call, arguments: dict, company_id: str) -> dict:
        from app.services.document_comparison_service import DocumentComparisonService
        
        try:
            doc1_id = arguments.get("doc1_id", "").strip()
            doc2_id = arguments.get("doc2_id", "").strip()
            doc1_b64 = arguments.get("doc1_base64", "")
            doc2_b64 = arguments.get("doc2_base64", "")
            doc1_name = arguments.get("doc1_name", "")
            doc2_name = arguments.get("doc2_name", "")
            
            async def get_doc_bytes_and_name(doc_id, b64_data, name):
                if doc_id:
                    upload_dir = "static/uploads"
                    for f in os.listdir(upload_dir):
                        if f.startswith(doc_id):
                            with open(os.path.join(upload_dir, f), "rb") as file_obj:
                                bytes_data = file_obj.read()
                                file_name = f.split('_', 1)[1] if '_' in f else f
                                return bytes_data, file_name
                    raise ValueError(f"Documento {doc_id} no encontrado")
                elif b64_data:
                    return self.safe_base64_decode(b64_data), name or "documento"
                else:
                    raise ValueError("Se requiere doc_id o doc_base64")
            
            doc1_bytes, doc1_final_name = await get_doc_bytes_and_name(doc1_id, doc1_b64, doc1_name)
            doc2_bytes, doc2_final_name = await get_doc_bytes_and_name(doc2_id, doc2_b64, doc2_name)
            result = await DocumentComparisonService.compare_documents(
                doc1_bytes, doc1_final_name,
                doc2_bytes, doc2_final_name
            )
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