import logging
import difflib
from typing import Dict, Any, List, Tuple
from app.services.file_processor import FileProcessor

logger = logging.getLogger("DocComparisonService")

class DocumentComparisonService:
    """Compara dos documentos (PDF, TXT, Excel, etc.) y muestra diferencias"""
    
    @staticmethod
    async def compare_documents(
        doc1_bytes: bytes,
        doc1_name: str,
        doc2_bytes: bytes,
        doc2_name: str
    ) -> Dict[str, Any]:
        """
        Compara el texto de dos documentos y devuelve similitud y diferencias.
        
        Returns:
            Dict con 'success', 'similarity', 'diff_summary', 'changes'
        """
        try:
            # Extraer texto de ambos
            text1 = await FileProcessor.extract_text(doc1_bytes, doc1_name)
            text2 = await FileProcessor.extract_text(doc2_bytes, doc2_name)
            
            if not text1 or not text2:
                return {"success": False, "message": "No se pudo extraer texto de uno o ambos documentos"}
            
            # Calcular similitud (ratio de secuencia)
            seq_matcher = difflib.SequenceMatcher(None, text1, text2)
            similarity = seq_matcher.ratio()
            
            # Generar diff legible (primeras 2000 caracteres)
            diff_lines = list(difflib.unified_diff(
                text1.splitlines(),
                text2.splitlines(),
                fromfile=doc1_name,
                tofile=doc2_name,
                lineterm=''
            ))
            
            diff_text = "\n".join(diff_lines[:100])  # límite de líneas
            if len(diff_lines) > 100:
                diff_text += f"\n... y {len(diff_lines) - 100} líneas más."
            
            # Resumen de cambios (estadísticas simples)
            added = sum(1 for line in diff_lines if line.startswith('+') and not line.startswith('+++'))
            removed = sum(1 for line in diff_lines if line.startswith('-') and not line.startswith('---'))
            
            return {
                "success": True,
                "similarity": round(similarity * 100, 2),
                "doc1_length": len(text1),
                "doc2_length": len(text2),
                "added_lines": added,
                "removed_lines": removed,
                "diff_preview": diff_text[:1500],  # limitar para no saturar
                "message": f"Los documentos tienen un {round(similarity*100,2)}% de similitud."
            }
            
        except Exception as e:
            logger.error(f"Error comparando documentos: {e}")
            return {"success": False, "message": f"Error: {str(e)}"}