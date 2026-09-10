from .vector_operations import purge_document, process_and_index, search_context
from .vision import analyze_visual_data
from .pdf_generator import create_report_pdf
from .chat_core import generate_venom_response
from .tools_definition import get_available_tools
from .chat_title import generate_chat_title

# mantener una clase VenomEngine con métodos estáticos que delegan
class VenomEngine:
    @staticmethod
    async def purge_document(doc_id: str, company_id: str) -> bool:
        return await purge_document(doc_id, company_id)

    @staticmethod
    async def process_and_index(file_bytes: bytes, filename: str, doc_id: str, company_id: str) -> bool:
        return await process_and_index(file_bytes, filename, doc_id, company_id)

    @staticmethod
    async def search_context(query: str, company_id: str) -> str:
        return await search_context(query, company_id)

    @staticmethod
    async def analyze_visual_data(image_bytes: bytes, user_query: str, groq_client=None) -> str:
        return await analyze_visual_data(image_bytes, user_query, groq_client)

    @staticmethod
    def create_report_pdf(title: str, content: str, company_id: str) -> bytes:
        return create_report_pdf(title, content, company_id)

    @staticmethod
    async def generate_venom_response(query: str, user_name: str, company_id: str,
                                       groq_client, db_session, file_bytes=None, history_db=None) -> str:
        return await generate_venom_response(query, user_name, company_id,
                                               groq_client, db_session, file_bytes, history_db)

    @staticmethod
    def get_available_tools():
        return get_available_tools()

    @staticmethod
    async def generate_chat_title(query: str, groq_client) -> str:
        return await generate_chat_title(query, groq_client)