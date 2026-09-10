# app/services/file_processor.py
import io
import logging
import chardet
from typing import Dict, Any, Optional, Union
import pandas as pd
from pypdf import PdfReader

logger = logging.getLogger("FileProcessor")

class FileProcessor:
    """
    Servicio para procesar diferentes tipos de archivos:
    - TXT (detección automática de encoding)
    - PDF (extracción de texto)
    - Excel (.xlsx, .xls)
    - CSV
    - (opcional) JSON, Markdown, etc.
    """
    
    @classmethod
    async def extract_text(cls, file_bytes: bytes, filename: str) -> str:
        """
        Extrae todo el texto legible de un archivo.
        
        Args:
            file_bytes: bytes del archivo
            filename: nombre del archivo (incluye extensión)
            
        Returns:
            str: Texto extraído (vacío si no se pudo)
        """
        filename_lower = filename.lower()
        
        try:
            if filename_lower.endswith('.pdf'):
                return await cls._extract_from_pdf(file_bytes)
            elif filename_lower.endswith('.txt'):
                return await cls._extract_from_txt(file_bytes)
            elif filename_lower.endswith(('.xlsx', '.xls')):
                return await cls._extract_from_excel(file_bytes)
            elif filename_lower.endswith('.csv'):
                return await cls._extract_from_csv(file_bytes)
            elif filename_lower.endswith('.json'):
                return await cls._extract_from_json(file_bytes)
            elif filename_lower.endswith('.md'):
                return await cls._extract_from_txt(file_bytes)  # Markdown como texto plano
            else:
                logger.warning(f"Extensión no soportada: {filename}")
                return f"[Archivo no procesable: {filename} - extensión no soportada]"
        except Exception as e:
            logger.error(f"Error extrayendo texto de {filename}: {e}")
            return f"[Error al procesar {filename}: {str(e)}]"
    
    @classmethod
    async def _extract_from_pdf(cls, file_bytes: bytes) -> str:
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts)
    
    @classmethod
    async def _extract_from_txt(cls, file_bytes: bytes) -> str:
        # Detectar encoding automáticamente
        encoding_info = chardet.detect(file_bytes)
        encoding = encoding_info.get('encoding', 'utf-8') if encoding_info else 'utf-8'
        try:
            return file_bytes.decode(encoding, errors='replace')
        except Exception:
            # Fallback a utf-8 con reemplazo
            return file_bytes.decode('utf-8', errors='replace')
    
    @classmethod
    async def _extract_from_excel(cls, file_bytes: bytes) -> str:
        df_dict = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None)
        all_text = []
        for sheet_name, df in df_dict.items():
            # Convertir hoja a texto tabular
            text = f"\n--- HOJA: {sheet_name} ---\n"
            text += df.to_string(index=False, max_rows=100, max_cols=20)
            all_text.append(text)
        return "\n".join(all_text)
    
    @classmethod
    async def _extract_from_csv(cls, file_bytes: bytes) -> str:
        # Probar con diferentes separadores y encoding
        try:
            # Detectar encoding
            encoding_info = chardet.detect(file_bytes)
            encoding = encoding_info.get('encoding', 'utf-8') if encoding_info else 'utf-8'
            
            # Intentar con separador coma
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding)
            except:
                # Probar punto y coma
                df = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding, sep=';')
            
            return df.to_string(index=False, max_rows=100, max_cols=20)
        except Exception as e:
            # Si falla, devolver como texto plano
            logger.warning(f"Error leyendo CSV con pandas, fallback a texto: {e}")
            text = await cls._extract_from_txt(file_bytes)
            return text
    
    @classmethod
    async def _extract_from_json(cls, file_bytes: bytes) -> str:
        import json
        try:
            text = file_bytes.decode('utf-8', errors='replace')
            data = json.loads(text)
            return json.dumps(data, indent=2, ensure_ascii=False)[:10000]  # límite
        except Exception as e:
            logger.warning(f"Error parseando JSON: {e}")
            return text[:10000]
    
    @classmethod
    async def get_metadata(cls, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """
        Obtiene metadatos del archivo sin extraer todo el texto.
        Útil para respuestas rápidas.
        """
        filename_lower = filename.lower()
        metadata = {
            "filename": filename,
            "size_bytes": len(file_bytes),
            "extension": filename.split('.')[-1] if '.' in filename else "unknown"
        }
        
        # Metadatos específicos por tipo
        if filename_lower.endswith(('.xlsx', '.xls')):
            try:
                excel_data = pd.ExcelFile(io.BytesIO(file_bytes))
                metadata["sheets"] = excel_data.sheet_names
                metadata["sheet_count"] = len(excel_data.sheet_names)
            except Exception as e:
                metadata["error"] = str(e)
        
        elif filename_lower.endswith('.csv'):
            try:
                # Detectar encoding
                encoding_info = chardet.detect(file_bytes)
                encoding = encoding_info.get('encoding', 'utf-8') if encoding_info else 'utf-8'
                df_sample = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding, nrows=5)
                metadata["columns"] = list(df_sample.columns)
                metadata["approx_rows"] = "desconocido"
            except:
                pass
        
        elif filename_lower.endswith('.pdf'):
            try:
                reader = PdfReader(io.BytesIO(file_bytes))
                metadata["pages"] = len(reader.pages)
                if reader.metadata:
                    for k, v in reader.metadata.items():
                        if v:
                            metadata[k] = str(v)
            except:
                pass
        
        elif filename_lower.endswith('.txt'):
            try:
                encoding_info = chardet.detect(file_bytes)
                metadata["detected_encoding"] = encoding_info.get('encoding', 'unknown') if encoding_info else 'unknown'
                metadata["confidence"] = encoding_info.get('confidence', 0) if encoding_info else 0
            except:
                pass
        
        return metadata
    
    @classmethod
    async def is_supported(cls, filename: str) -> bool:
        """Verifica si la extensión está soportada para extracción de texto"""
        supported_extensions = ('.pdf', '.txt', '.xlsx', '.xls', '.csv', '.json', '.md')
        return filename.lower().endswith(supported_extensions)