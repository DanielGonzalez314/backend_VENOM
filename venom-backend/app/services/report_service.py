# app/services/report_service.py
import io
import logging
import os
from datetime import datetime
from typing import Optional, Union
from fpdf import FPDF
import base64

logger = logging.getLogger("ReportService")

class ReportService:
    """
    Servicio para generar reportes PDF.
    Soporta generación de PDF a partir de título y contenido,
    con formato básico y posibilidad de devolver bytes o base64.
    """
    
    @staticmethod
    async def generate_pdf(
        title: str,
        content: str,
        company_id: Optional[str] = None,
        return_base64: bool = False
    ) -> Union[bytes, str]:
        """
        Genera un PDF con el título y contenido proporcionados.
        
        Args:
            title: Título del reporte
            content: Contenido del reporte (texto plano, se ajustará automáticamente)
            company_id: Identificador de la empresa (opcional, para personalizar)
            return_base64: Si True devuelve string base64, si False devuelve bytes
            
        Returns:
            bytes o base64 string del PDF generado
        """
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # Configurar fuente
            pdf.set_font("Arial", "B", 16)
            
            # Encabezado con company_id si existe
            if company_id:
                pdf.cell(0, 10, f"VENOM ANALYTICS - {company_id}", 0, 1, 'C')
                pdf.ln(5)
            else:
                pdf.cell(0, 10, "VENOM ANALYTICS", 0, 1, 'C')
                pdf.ln(5)
            
            # Título
            pdf.set_font("Arial", "B", 14)
            pdf.multi_cell(0, 10, title, align='L')
            pdf.ln(5)
            
            # Fecha
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 5, f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, 'L')
            pdf.ln(10)
            
            # Contenido principal
            pdf.set_font("Arial", size=11)
            
            # Escapar caracteres no latin1 (FPDF usa latin1 por defecto)
            safe_content = content.encode('latin-1', 'replace').decode('latin-1')
            
            # Dividir el contenido en líneas y agregar al PDF
            pdf.multi_cell(0, 8, safe_content)
            
            # Pie de página
            pdf.set_y(-20)
            pdf.set_font("Arial", "I", 8)
            pdf.cell(0, 10, f"Página {pdf.page_no()}", 0, 0, 'C')
            
            # Obtener bytes
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            
            logger.info(f"✅ PDF generado: '{title}' para empresa {company_id or 'desconocida'}, tamaño={len(pdf_bytes)} bytes")
            
            if return_base64:
                return base64.b64encode(pdf_bytes).decode('utf-8')
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"❌ Error generando PDF: {e}")
            # Devolver un PDF de error simple
            return await ReportService._generate_error_pdf(title, str(e), return_base64)
    
    @staticmethod
    async def generate_report_from_dataframe(
        df,
        title: str,
        company_id: Optional[str] = None,
        include_stats: bool = True
    ) -> bytes:
        """
        Genera un PDF a partir de un DataFrame de pandas (útil para reportes de datos).
        
        Args:
            df: DataFrame de pandas con los datos
            title: Título del reporte
            company_id: ID de empresa
            include_stats: Incluir estadísticas básicas
            
        Returns:
            bytes del PDF
        """
        try:
            import pandas as pd
            
            # Crear contenido textual a partir del DataFrame
            content = []
            
            if include_stats and len(df) > 0:
                content.append("=== ESTADÍSTICAS BÁSICAS ===")
                # Columnas numéricas
                num_cols = df.select_dtypes(include=['number']).columns
                if len(num_cols) > 0:
                    content.append(df[num_cols].describe().to_string())
                content.append("\n")
            
            content.append("=== DATOS (muestra) ===")
            # Limitamos a 50 filas para no saturar el PDF
            sample = df.head(50) if len(df) > 50 else df
            content.append(sample.to_string(index=False, max_cols=10))
            
            if len(df) > 50:
                content.append(f"\n\n... y {len(df) - 50} filas más (limitado por legibilidad)")
            
            full_content = "\n\n".join(content)
            
            return await ReportService.generate_pdf(title, full_content, company_id)
            
        except Exception as e:
            logger.error(f"Error generando PDF desde DataFrame: {e}")
            raise
    
    @staticmethod
    async def _generate_error_pdf(title: str, error_msg: str, return_base64: bool = False) -> Union[bytes, str]:
        """Genera un PDF indicando que hubo un error en la generación."""
        error_content = f"""
ERROR AL GENERAR EL REPORTE

Título solicitado: {title}

Detalle del error:
{error_msg}

Por favor, contacte al administrador del sistema VENOM.
        """.strip()
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "VENOM - Error en Reporte", 0, 1, 'C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        safe_content = error_content.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 8, safe_content)
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        
        if return_base64:
            return base64.b64encode(pdf_bytes).decode('utf-8')
        return pdf_bytes
    
    @staticmethod
    async def save_pdf_to_file(pdf_bytes: bytes, filename: str, directory: str = "reports") -> str:
        """
        Guarda un PDF en disco.
        
        Args:
            pdf_bytes: Bytes del PDF
            filename: Nombre del archivo (debe terminar en .pdf)
            directory: Directorio donde guardar (por defecto 'reports')
            
        Returns:
            Ruta completa del archivo guardado
        """
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, filename)
        with open(filepath, "wb") as f:
            f.write(pdf_bytes)
        logger.info(f"PDF guardado en: {filepath}")
        return filepath