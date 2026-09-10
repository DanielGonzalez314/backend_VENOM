# app/services/venom_engine.py
import io
import base64
import logging
import asyncio
import json
from typing import List, Optional, Any
import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader

# Importaciones de los nuevos servicios
from app.services.file_processor import FileProcessor
from app.services.vision_service import VisionService
from app.services.report_service import ReportService

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VenomEngine")

# Configuración de Chroma DB (persistente)
chroma_client = chromadb.PersistentClient(path="./venom_knowledge")
default_ef = embedding_functions.DefaultEmbeddingFunction()
collection = chroma_client.get_or_create_collection(
    name="company_knowledge",
    embedding_function=default_ef
)

class VenomEngine:
    
    # ==================== 1. GESTIÓN VECTORIAL ====================
    @staticmethod
    async def purge_document(doc_id: str, company_id: str) -> bool:
        """Elimina todos los fragmentos de un documento de la base vectorial."""
        try:
            cid = str(company_id).strip()
            collection.delete(
                where={
                    "$and": [
                        {"source": doc_id},
                        {"company_id": cid}
                    ]
                }
            )
            logger.info(f"🗑️ Purga exitosa: {doc_id} para empresa {cid}")
            return True
        except Exception as e:
            logger.error(f"❌ Error en Purga: {e}")
            return False

    # ==================== 2. INGESTA (con FileProcessor) ====================
    @staticmethod
    async def process_and_index(file_bytes: bytes, filename: str, doc_id: str, company_id: str) -> bool:
        """
        Indexa un archivo en la base vectorial.
        Soporta PDF, TXT, Excel, CSV, JSON.
        """
        cid = str(company_id).strip()
        try:
            # Extraer texto usando el servicio FileProcessor
            text = await FileProcessor.extract_text(file_bytes, filename)
            if not text or not text.strip():
                logger.warning(f"⚠️ No se pudo extraer texto de {filename}")
                return False

            # Fragmentar (chunking)
            chunk_size, overlap = 1000, 200
            chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size - overlap)]
            if not chunks:
                return False

            # Agregar a ChromaDB
            collection.add(
                documents=chunks,
                metadatas=[{"source": doc_id, "company_id": cid} for _ in chunks],
                ids=[f"{doc_id}_{i}" for i in range(len(chunks))]
            )
            logger.info(f"✅ Indexado {len(chunks)} fragmentos de {filename} (doc_id={doc_id})")
            return True
        except Exception as e:
            logger.error(f"❌ Error en indexación de {filename}: {e}", exc_info=True)
            raise e

    # ==================== 3. BÚSQUEDA RAG ====================
    @staticmethod
    async def search_context(query: str, company_id: str) -> str:
        """Recupera fragmentos relevantes para la consulta desde la base vectorial."""
        try:
            cid = str(company_id).strip()
            results = collection.query(
                query_texts=[query],
                n_results=5,
                where={"company_id": cid}
            )
            if results['documents'] and results['documents'][0]:
                content = "\n".join(results['documents'][0])
                logger.info(f"🔍 RAG: {len(results['documents'][0])} fragmentos recuperados para {cid}")
                return content
            logger.warning(f"🔍 RAG: Sin contexto para {cid} en la consulta: {query[:50]}")
            return ""
        except Exception as e:
            logger.error(f"⚠️ Error en búsqueda RAG: {e}")
            return ""

    # ==================== 4. VISIÓN (delegado a VisionService con fallback robusto) ====================
    @staticmethod
    async def analyze_visual_data(image_bytes: bytes, user_query: str, groq_client=None) -> str:
        """
        Analiza una imagen usando VisionService.
        Si VisionService falla (por falta de API key o error), devuelve metadatos básicos.
        """
        try:
            return await VisionService.analyze_image(image_bytes, user_query)
        except Exception as e:
            logger.error(f"❌ Error en VisionService: {e}", exc_info=True)
            # Fallback: información mínima de la imagen
            try:
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(image_bytes))
                return f"""
[ANÁLISIS LOCAL DE IMAGEN]
No se pudo usar el servicio de visión avanzada (Hugging Face no configurado o error).
Metadatos de la imagen:
- Formato: {img.format}
- Dimensiones: {img.width} x {img.height}
- Modo: {img.mode}
- Peso: {len(image_bytes)} bytes

Consulta del usuario: {user_query}
Para análisis detallado, configura HUGGINGFACE_API_KEY en .env.
"""
            except:
                return f"No se pudo analizar la imagen (error interno). Consulta: {user_query}"

    # ==================== 5. REPORTE PDF (delegado a ReportService) ====================
    @staticmethod
    def create_report_pdf(title: str, content: str, company_id: str) -> bytes:
        """
        Genera un PDF usando ReportService.
        Método síncrono para mantener compatibilidad con llamadas existentes.
        """
        loop = asyncio.get_event_loop()
        if loop.is_running():
            try:
                import nest_asyncio
                nest_asyncio.apply()
                pdf_bytes = loop.run_until_complete(
                    ReportService.generate_pdf(title, content, company_id, return_base64=False)
                )
            except ImportError:
                pdf_bytes = asyncio.run(
                    ReportService.generate_pdf(title, content, company_id, return_base64=False)
                )
        else:
            pdf_bytes = asyncio.run(
                ReportService.generate_pdf(title, content, company_id, return_base64=False)
            )
        return pdf_bytes

    # ==================== 6. CEREBRO CENTRAL (con todas las herramientas) ====================
    @staticmethod
    async def generate_venom_response(
        query: str,
        user_name: str,
        company_id: str,
        groq_client,
        db_session,  # Se mantiene por compatibilidad
        file_bytes: Optional[bytes] = None,
        history_db: Optional[List[Any]] = None
    ) -> str:
        """
        Genera una respuesta inteligente de VENOM usando RAG, visión (si aplica) y herramientas.
        """
        cid = str(company_id).strip()

        # 1. Contexto RAG
        context = await VenomEngine.search_context(query, cid)

        # 2. Análisis de imagen si se adjuntó un archivo que es imagen
        visual_info = ""
        if file_bytes and len(file_bytes) > 0:
            is_img = await VisionService.is_image(file_bytes)
            if is_img:
                visual_info = await VenomEngine.analyze_visual_data(file_bytes, query, groq_client)
            else:
                visual_info = "El usuario adjuntó un archivo que no es una imagen (documento). Para procesarlo, se debe usar la herramienta 'process_file'."

        # 3. Construcción del System Prompt
        system_prompt = (
            f"ERES VENOM, LA UNIDAD DE IA DE LA EMPRESA {cid}.\n"
            f"NOMBRE DEL USUARIO: {user_name}.\n\n"
            f"REGLA CRÍTICA: Tienes acceso total al DATA LAKE de la empresa. No digas que no puedes leer archivos.\n"
            f"--- CONTENIDO DEL DATA LAKE (CONOCIMIENTO ACTUAL) ---\n"
            f"{context if context else 'El Data Lake no devolvió resultados específicos para esta consulta.'}\n"
            f"--- FIN DEL CONOCIMIENTO ---\n\n"
        )
        if visual_info:
            system_prompt += f"VISIÓN ACTIVA: El usuario adjuntó una imagen. Contenido analizado: {visual_info}\n"

        # 4. Mensajes del historial (máximo 5 últimos)
        messages = [{"role": "system", "content": system_prompt}]
        if history_db:
            for msg in history_db[-5:]:
                messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": query})

        try:
            # 5. Llamada inicial a Groq con herramientas
            completion = await groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=VenomEngine.get_available_tools(),
                tool_choice="auto",
                temperature=0.7
            )

            response_msg = completion.choices[0].message

            # 6. Si la IA solicita usar herramientas, las ejecutamos con el Dispatcher
            if response_msg.tool_calls:
                from app.services.dispatcher import VenomDispatcher
                tool_results = await VenomDispatcher.execute_tools(response_msg.tool_calls, cid)

                # Agregar la respuesta de la IA y los resultados de las herramientas al historial
                messages.append(response_msg)
                for res in tool_results:
                    # Asegurarse de que el contenido es string
                    output_content = res["output"]
                    if isinstance(output_content, dict):
                        output_content = json.dumps(output_content, ensure_ascii=False)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": res["tool_call_id"],
                        "name": res["name"],
                        "content": output_content
                    })

                # Segunda llamada a Groq para generar la respuesta final
                final = await groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.7
                )
                return final.choices[0].message.content

            # Sin herramientas, devolver respuesta directa
            return response_msg.content

        except Exception as e:
            logger.error(f"❌ Error en cerebro Venom: {e}", exc_info=True)
            return "Lo siento, tuve un problema interno. ¿Podrías reformular tu pregunta?"

    # ==================== 7. DEFINICIÓN DE HERRAMIENTAS (TOOLS) ====================
    @staticmethod
    def get_available_tools():
        """Devuelve la lista de herramientas disponibles para que la IA las use."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "generate_report_pdf",
                    "description": "Genera un reporte en formato PDF con el título y contenido especificados.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Título del reporte"},
                            "content": {"type": "string", "description": "Contenido detallado en texto plano"}
                        },
                        "required": ["title", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Busca información actualizada en internet usando el motor Tavily.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Término de búsqueda"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_email",
                    "description": "Envía un correo electrónico a un destinatario.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "to": {"type": "string", "description": "Dirección de correo del destinatario"},
                            "subject": {"type": "string", "description": "Asunto del mensaje"},
                            "body": {"type": "string", "description": "Cuerpo del mensaje en texto plano"}
                        },
                        "required": ["to", "subject", "body"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "process_file",
                    "description": "Extrae el texto de un archivo (PDF, Excel, CSV, TXT, JSON) subido por el usuario.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_base64": {"type": "string", "description": "Contenido del archivo en base64"},
                            "filename": {"type": "string", "description": "Nombre del archivo con extensión"}
                        },
                        "required": ["file_base64", "filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_image",
                    "description": "Analiza una imagen y devuelve una descripción textual de su contenido.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "image_base64": {"type": "string", "description": "Imagen en base64"},
                            "query": {"type": "string", "description": "Pregunta específica sobre la imagen (opcional)"}
                        },
                        "required": ["image_base64"]
                    }
                }
            }
        ]

    # ==================== 8. GENERACIÓN DE TÍTULOS PARA CHATS ====================
    @staticmethod
    async def generate_chat_title(query: str, groq_client) -> str:
        """Genera un título corto para un chat basado en la primera consulta."""
        try:
            resp = await groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": f"Genera un título de máximo 5 palabras para este mensaje: {query}"}],
                max_tokens=15,
                temperature=0.5
            )
            title = resp.choices[0].message.content.strip().strip('"')
            if len(title) > 50:
                title = title[:47] + "..."
            return title
        except Exception:
            return query[:30]