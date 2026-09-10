# app/services/dispatcher.py
import json
import logging
import base64
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class VenomDispatcher:
    """
    Dispatcher de herramientas para VENOM.
    Ejecuta las funciones solicitadas por la IA y devuelve resultados.
    """

    @staticmethod
    def safe_base64_decode(data: str) -> bytes:
        """Decodifica Base64 añadiendo automáticamente el padding faltante."""
        # Añade los caracteres '=' necesarios para que la longitud sea múltiplo de 4
        padding = 4 - (len(data) % 4)
        if padding != 4:
            data += '=' * padding
        return base64.b64decode(data)

    @staticmethod
    async def execute_tools(tool_calls: List[Any], company_id: str) -> List[Dict[str, Any]]:
        """
        Ejecuta múltiples herramientas solicitadas por la IA.

        Args:
            tool_calls: Lista de llamadas a herramientas del modelo
            company_id: ID de la empresa para contexto

        Returns:
            Lista de resultados con tool_call_id, name y output
        """
        results = []

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                logger.error(f"Error parseando argumentos para {function_name}")
                arguments = {}
            except Exception as e:
                logger.error(f"Error inesperado: {e}")
                arguments = {}

            logger.info(f"🛠️ Ejecutando herramienta: {function_name} | Args: {arguments}")

            # ------------------------------------------------------------
            # 1. GENERAR REPORTE PDF
            # ------------------------------------------------------------
            if function_name == "generate_report_pdf":
                try:
                    from app.services.report_service import ReportService

                    title = arguments.get("title", "Reporte VENOM")
                    content = arguments.get("content", "Sin contenido")

                    pdf_bytes = await ReportService.generate_pdf(
                        title=title,
                        content=content,
                        company_id=company_id,
                        return_base64=False
                    )

                    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

                    # Resultado como dict, luego lo convertimos a string
                    output_data = {
                        "success": True,
                        "message": "PDF generado exitosamente",
                        "data": pdf_base64,
                        "filename": f"reporte_{company_id}_{title[:30].replace(' ', '_')}.pdf"
                    }
                    results.append({
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "output": json.dumps(output_data, ensure_ascii=False)  # Convertir a string
                    })
                    logger.info(f"✅ PDF generado para empresa {company_id}")

                except Exception as e:
                    logger.error(f"❌ Error generando PDF: {e}", exc_info=True)
                    results.append({
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "output": json.dumps({"success": False, "message": f"Error técnico: {str(e)}"})
                    })

            # ------------------------------------------------------------
            # 2. BÚSQUEDA WEB (Tavily)
            # ------------------------------------------------------------
            elif function_name == "web_search":
                try:
                    from app.services.web_search_service import WebSearchService

                    query = arguments.get("query", "").strip()
                    if not query:
                        raise ValueError("Falta el parámetro 'query'")

                    result = await WebSearchService.search(query, max_results=5)

                    if result.get("success"):
                        output_data = {
                            "success": True,
                            "data": result["results"]  # texto formateado
                        }
                    else:
                        output_data = {
                            "success": False,
                            "message": result.get("error", "Error desconocido")
                        }
                    results.append({
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "output": json.dumps(output_data, ensure_ascii=False)
                    })
                    logger.info(f"✅ Búsqueda web completada para: {query}")

                except Exception as e:
                    logger.error(f"❌ Error en búsqueda web: {e}", exc_info=True)
                    results.append({
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "output": json.dumps({"success": False, "message": str(e)})
                    })

            # ------------------------------------------------------------
            # 3. ENVÍO DE CORREO (SendGrid)
            # ------------------------------------------------------------
            elif function_name == "send_email":
                try:
                    from app.services.email_service import EmailService

                    to = arguments.get("to", "").strip()
                    subject = arguments.get("subject", "").strip()
                    body = arguments.get("body", "").strip()

                    if not to or not subject or not body:
                        raise ValueError("Faltan parámetros requeridos: to, subject, body")

                    result = await EmailService.send_email(to, subject, body)

                    output_data = {
                        "success": result["success"],
                        "message": result["message"]
                    }
                    results.append({
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "output": json.dumps(output_data, ensure_ascii=False)
                    })
                    if result["success"]:
                        logger.info(f"✅ Correo enviado a {to}")
                    else:
                        logger.warning(f"❌ Fallo en envío de correo: {result['message']}")

                except Exception as e:
                    logger.error(f"❌ Error enviando email: {e}", exc_info=True)
                    results.append({
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "output": json.dumps({"success": False, "message": str(e)})
                    })

            # ------------------------------------------------------------
            # 4. PROCESAR ARCHIVO (extraer texto)
            # ------------------------------------------------------------
            elif function_name == "process_file":
                try:
                    from app.services.file_processor import FileProcessor

                    file_b64 = arguments.get("file_base64", "")
                    filename = arguments.get("filename", "archivo_desconocido")

                    if not file_b64:
                        raise ValueError("No se proporcionó el archivo en base64 (campo 'file_base64')")

                    # Usamos safe_base64_decode para evitar padding errors
                    file_bytes = VenomDispatcher.safe_base64_decode(file_b64)

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
                    results.append({
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "output": json.dumps(output_data, ensure_ascii=False)
                    })
                    logger.info(f"✅ Archivo procesado: {filename} | {len(text)} caracteres extraídos")

                except Exception as e:
                    logger.error(f"❌ Error procesando archivo: {e}", exc_info=True)
                    results.append({
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "output": json.dumps({"success": False, "message": str(e)})
                    })

            # ------------------------------------------------------------
            # 5. ANALIZAR IMAGEN (visión)
            # ------------------------------------------------------------
            elif function_name == "analyze_image":
                try:
                    from app.services.vision_service import VisionService

                    image_b64 = arguments.get("image_base64", "")
                    user_query = arguments.get("query", "Describe esta imagen")

                    if not image_b64:
                        raise ValueError("No se proporcionó la imagen en base64 (campo 'image_base64')")

                    # Decodificación segura
                    image_bytes = VenomDispatcher.safe_base64_decode(image_b64)

                    description = await VisionService.analyze_image(image_bytes, user_query)

                    output_data = {
                        "success": True,
                        "description": description
                    }
                    results.append({
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "output": json.dumps(output_data, ensure_ascii=False)
                    })
                    logger.info(f"✅ Imagen analizada | Query: {user_query[:50]}")

                except Exception as e:
                    logger.error(f"❌ Error analizando imagen: {e}", exc_info=True)
                    results.append({
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "output": json.dumps({"success": False, "message": str(e)})
                    })

            # ------------------------------------------------------------
            # HERRAMIENTA NO RECONOCIDA
            # ------------------------------------------------------------
            else:
                logger.warning(f"⚠️ Herramienta no reconocida: {function_name}")
                results.append({
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "output": json.dumps({"success": False, "message": f"Herramienta '{function_name}' no implementada"})
                })

        return results