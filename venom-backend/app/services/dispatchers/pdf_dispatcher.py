import os
import uuid
import json
from datetime import datetime
from .base import BaseDispatcher

class PdfDispatcher(BaseDispatcher):
    def can_handle(self, function_name: str) -> bool:
        return function_name == "generate_report_pdf"
    
    async def execute(self, tool_call, arguments: dict, company_id: str) -> dict:
        from app.services.report_service import ReportService
        
        try:
            title = arguments.get("title", "Reporte VENOM")
            content = arguments.get("content", "Sin contenido")
            pdf_bytes = await ReportService.generate_pdf(
                title=title,
                content=content,
                company_id=company_id,
                return_base64=False
            )
            temp_dir = "static/temp"
            os.makedirs(temp_dir, exist_ok=True)
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).replace(' ', '_')
            unique_id = uuid.uuid4().hex[:8]
            filename = f"pdf_{company_id}_{safe_title}_{unique_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, "wb") as f:
                f.write(pdf_bytes)
            pdf_url = f"/static/temp/{filename}"
            output_data = {
                "success": True,
                "message": "PDF generado exitosamente",
                "url": pdf_url,
                "filename": filename
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
                "output": json.dumps({"success": False, "message": f"Error técnico: {str(e)}"})
            }