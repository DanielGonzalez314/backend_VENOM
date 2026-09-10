import pytest
from app.services.report_service import ReportService

@pytest.mark.asyncio
async def test_generate_pdf_returns_bytes():
    pdf_bytes = await ReportService.generate_pdf("Título", "Contenido", company_id="test")
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b'%PDF')  # Magic number PDF

@pytest.mark.asyncio
async def test_generate_pdf_with_base64():
    b64 = await ReportService.generate_pdf("Título", "Texto", return_base64=True)
    assert isinstance(b64, str)
    assert len(b64) > 100