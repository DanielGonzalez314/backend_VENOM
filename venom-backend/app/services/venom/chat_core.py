# app/services/venom/chat_core.py
import json
import logging
from typing import List, Optional, Any
from .vector_operations import search_context
from .vision import analyze_visual_data
from .tools_definition import get_available_tools
from app.services.vision_service import VisionService

logger = logging.getLogger("VenomEngine")

async def generate_venom_response(
    query: str,
    user_name: str,
    company_id: str,
    groq_client,
    db_session,
    file_bytes: Optional[bytes] = None,
    history_db: Optional[List[Any]] = None
) -> str:
    cid = str(company_id).strip()

    context = await search_context(query, cid)

    visual_info = ""
    if file_bytes and len(file_bytes) > 0:
        is_img = await VisionService.is_image(file_bytes)
        if is_img:
            visual_info = await analyze_visual_data(file_bytes, query, groq_client)
        else:
            visual_info = "El usuario adjuntó un archivo que no es una imagen (documento). Usa la herramienta 'process_file'."

    # System prompt actualizado con herramientas MCP
    system_prompt = (
        f"ERES VENOM, IA DE LA EMPRESA {cid}.\n"
        f"USUARIO: {user_name}.\n\n"
        f"--- CONTEXTO DEL DATA LAKE ---\n"
        f"{context if context else 'No hay contexto específico para esta consulta.'}\n"
        f"--- FIN CONTEXTO ---\n\n"
        f"REGLAS:\n"
        f"- Para archivos ya subidos (data lake): usa 'generate_chart' con 'document_id', 'compare_documents' con IDs, o 'list_documents'.\n"
        f"- 'process_file' SOLO para archivos adjuntos nuevos (requiere base64 válido).\n\n"
        f"HERRAMIENTAS MCP DISPONIBLES (cada una para una acción concreta):\n"
        f"- explorer_open: abre el explorador en una carpeta. Parámetro: 'path'.\n"
        f"- explorer_list: lista el contenido de un directorio. Parámetro: 'path'.\n"
        f"- explorer_create_folder: crea una nueva carpeta. Parámetro: 'path'.\n"
        f"- explorer_create_file: crea un archivo (contenido opcional). Parámetros: 'path', 'content'.\n"
        f"- explorer_delete: elimina un archivo o carpeta. Parámetro: 'path'.\n"
        f"- explorer_move: mueve o renombra. Parámetros: 'source', 'destination'.\n"
        f"- explorer_read: lee el contenido de un archivo de texto. Parámetro: 'path'.\n"
        f"- mcp_music: controla la música. Acciones: play, add_to_queue, pause, resume, stop, next, status.\n"
        f"- mcp_apps: abre o cierra aplicaciones (start/kill). Parámetros: 'action', 'app_name'.\n"
        f"- mcp_system: estadísticas del sistema (stats/processes). Parámetro: 'action'.\n"
        f"- mcp_windows: controla ventanas (minimize, maximize, close, focus). Parámetros: 'action', 'title'.\n\n"
        f"NO DES EXPLICACIONES TEXTUALES; USA DIRECTAMENTE LA HERRAMIENTA CORRESPONDIENTE.\n"
    )
    if visual_info:
        system_prompt += f"VISIÓN: {visual_info}\n"

    messages = [{"role": "system", "content": system_prompt}]
    if history_db:
        for msg in history_db[-5:]:
            messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": query})

    try:
        completion = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=get_available_tools(),
            tool_choice="auto",
            temperature=0.7
        )

        response_msg = completion.choices[0].message

        if response_msg.tool_calls:
            # ✅ CORRECCIÓN: instanciar el dispatcher antes de usarlo
            from app.services.dispatchers import VenomDispatcher
            dispatcher = VenomDispatcher()
            tool_results = await dispatcher.execute_tools(response_msg.tool_calls, cid)

            messages.append(response_msg)
            for res in tool_results:
                output_content = res["output"]
                if isinstance(output_content, dict):
                    output_content = json.dumps(output_content, ensure_ascii=False)
                messages.append({
                    "role": "tool",
                    "tool_call_id": res["tool_call_id"],
                    "name": res["name"],
                    "content": output_content
                })

            final = await groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7
            )
            final_content = final.choices[0].message.content

            # Extraer URL del PDF si se generó
            pdf_url = None
            for res in tool_results:
                if res["name"] == "generate_report_pdf":
                    try:
                        output_data = json.loads(res["output"])
                        if output_data.get("success") and output_data.get("url"):
                            pdf_url = output_data["url"]
                            break
                    except:
                        pass
            if pdf_url:
                final_content += f"\n\n[VENOM_PDF_URL]{pdf_url}[/VENOM_PDF_URL]"

            # Extraer gráfico en Base64 si se generó
            chart_base64 = None
            for res in tool_results:
                if res["name"] == "generate_chart":
                    try:
                        output_data = json.loads(res["output"])
                        if output_data.get("success") and output_data.get("image_base64"):
                            chart_base64 = output_data["image_base64"]
                            break
                    except:
                        pass
            if chart_base64:
                final_content += f"\n\n[VENOM_CHART_BASE64]{chart_base64}[/VENOM_CHART_BASE64]"

            return final_content

        return response_msg.content

    except Exception as e:
        logger.error(f"❌ Error en cerebro Venom: {e}", exc_info=True)
        return "Lo siento, tuve un problema interno. ¿Podrías reformular tu pregunta?"