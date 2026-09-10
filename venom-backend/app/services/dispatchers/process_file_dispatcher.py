import json
import re
from .base import BaseDispatcher

class ProcessFileDispatcher(BaseDispatcher):
    def can_handle(self, function_name: str) -> bool:
        return function_name == "process_file"
    
    async def execute(self, tool_call, arguments: dict, company_id: str) -> dict:
        from app.services.file_processor import FileProcessor
        
        try:
            file_b64 = arguments.get("file_base64", "")
            filename = arguments.get("filename", "archivo_desconocido")
            if not file_b64:
                raise ValueError("No se proporcionó el archivo en base64")
            if not re.match(r'^[A-Za-z0-9+/]+=*$', file_b64) or len(file_b64) < 100:
                raise ValueError("El campo 'file_base64' no es un base64 válido. Para documentos ya subidos usa 'document_id' en otras herramientas.")
            file_bytes = self.safe_base64_decode(file_b64)
            text = await FileProcessor.extract_text(file_bytes, filename)
            metadata = await FileProcessor.get_metadata(file_bytes, filename)
            output_data = {
                "success": True,
                "data": {
                    "text": text[:5000],
                    "metadata": metadata,
                    "full_text_length": len(text)
                }
            }
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