# tests/test_chart_service.py
import pytest
import pandas as pd
import io
import matplotlib
matplotlib.use('Agg')  # Evita GUI backend en entornos headless
from app.services.chart_service import ChartService

@pytest.mark.asyncio
async def test_generate_chart_with_valid_data():
    df = pd.DataFrame({"Mes": ["Ene", "Feb", "Mar"], "Ventas": [100, 150, 200]})
    excel_bytes = io.BytesIO()
    df.to_excel(excel_bytes, index=False)
    excel_bytes.seek(0)
    result = await ChartService.generate_chart(
        file_bytes=excel_bytes.read(),
        filename="test.xlsx",
        x_column="Mes",
        y_column="Ventas",
        chart_type="bar"
    )
    assert result["success"] is True
    assert "image_base64" in result
    assert result["data_points"] == 3

@pytest.mark.asyncio
async def test_generate_chart_missing_column():
    df = pd.DataFrame({"Mes": ["Ene", "Feb"], "Ventas": [100, 150]})
    excel_bytes = io.BytesIO()
    df.to_excel(excel_bytes, index=False)
    excel_bytes.seek(0)
    result = await ChartService.generate_chart(
        file_bytes=excel_bytes.read(),
        filename="test.xlsx",
        x_column="Mes",
        y_column="Existente"   # columna inexistente
    )
    assert result["success"] is False
    # Mensaje puede variar, buscamos palabras clave
    assert any(word in result["message"].lower() for word in ["no encontrada", "no existe", "existente"])