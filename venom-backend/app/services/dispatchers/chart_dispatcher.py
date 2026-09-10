import json
import os
from .base import BaseDispatcher

class ChartDispatcher(BaseDispatcher):
    def can_handle(self, function_name: str) -> bool:
        return function_name == "generate_chart"
    
    async def execute(self, tool_call, arguments: dict, company_id: str) -> dict:
        from app.services.chart_service import ChartService
        
        try:
            document_id = arguments.get("document_id", "").strip()
            file_b64 = arguments.get("file_base64", "")
            filename = arguments.get("filename", "")
            x_column = arguments.get("x_column", "")
            y_column = arguments.get("y_column", "")
            chart_type = arguments.get("chart_type", "bar")
            title = arguments.get("title", "Gráfico generado por VENOM")
            
            file_bytes = None
            actual_filename = filename
            upload_dir = "static/uploads"
            
            if document_id:
                found = False
                if os.path.exists(upload_dir):
                    for f in os.listdir(upload_dir):
                        if f.startswith(document_id):
                            with open(os.path.join(upload_dir, f), "rb") as file_obj:
                                file_bytes = file_obj.read()
                            actual_filename = f.split('_', 1)[1] if '_' in f else f
                            found = True
                            break
                    if not found:
                        target_name = document_id.replace(' ', '_')
                        for f in os.listdir(upload_dir):
                            if '_' in f:
                                _, name = f.split('_', 1)
                                if name.lower() == target_name.lower() or name == document_id:
                                    with open(os.path.join(upload_dir, f), "rb") as file_obj:
                                        file_bytes = file_obj.read()
                                    actual_filename = name
                                    found = True
                                    break
                if not found:
                    raise ValueError(f"No se encontró documento con ID o nombre: {document_id}")
            elif file_b64:
                file_bytes = self.safe_base64_decode(file_b64)
                if not actual_filename:
                    actual_filename = "archivo.csv"
            else:
                raise ValueError("Se requiere document_id o file_base64")
            
            if not x_column or not y_column:
                raise ValueError("Faltan columnas x_column y/o y_column")
            
            result = await ChartService.generate_chart(
                file_bytes=file_bytes,
                filename=actual_filename,
                x_column=x_column,
                y_column=y_column,
                chart_type=chart_type,
                title=title
            )
            if result.get("success"):
                output_data = {
                    "success": True,
                    "message": result["message"],
                    "image_base64": result["image_base64"],
                    "data_points": result.get("data_points", 0)
                }
            else:
                output_data = {"success": False, "message": result.get("message", "Error desconocido")}
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