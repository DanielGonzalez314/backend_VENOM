import asyncio
from app.services.report_service import ReportService

def create_report_pdf(title: str, content: str, company_id: str) -> bytes:
    """Genera un PDF usando ReportService (método síncrono para compatibilidad)."""
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