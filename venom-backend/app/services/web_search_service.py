# app/services/web_search_service.py
import os
import logging
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger("WebSearchService")

class WebSearchService:
    """
    Servicio para realizar búsquedas en internet usando exclusivamente Tavily.
    Registro gratuito en https://tavily.com (1000 búsquedas/mes).
    """
    
    TAVILY_API_URL = "https://api.tavily.com/search"
    
    @classmethod
    async def search(
        cls,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_answer: bool = True,
        include_raw_content: bool = False
    ) -> Dict[str, Any]:
        """
        Realiza una búsqueda web usando Tavily.
        
        Args:
            query: Término de búsqueda
            max_results: Número máximo de resultados (1-10)
            search_depth: "basic" o "advanced"
            include_answer: Incluir resumen automático
            include_raw_content: Incluir contenido crudo de la página
            
        Returns:
            dict con "success" y "results" (texto formateado) o "error"
        """
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return {
                "success": False,
                "error": "Tavily no está configurado. Agrega TAVILY_API_KEY en el archivo .env (obténla gratis en tavily.com)"
            }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    cls.TAVILY_API_URL,
                    json={
                        "api_key": api_key,
                        "query": query,
                        "max_results": min(max_results, 10),
                        "search_depth": search_depth,
                        "include_answer": include_answer,
                        "include_raw_content": include_raw_content
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    # Respuesta resumida (si existe)
                    answer = data.get("answer", "")
                    
                    # Lista de resultados detallados
                    for item in data.get("results", []):
                        results.append({
                            "title": item.get("title", ""),
                            "url": item.get("url", ""),
                            "content": item.get("content", ""),
                            "score": item.get("score", 0)
                        })
                    
                    formatted = cls._format_results(query, results, answer)
                    logger.info(f"✅ Búsqueda Tavily: '{query}' -> {len(results)} resultados")
                    return {"success": True, "results": formatted}
                else:
                    error_detail = response.text
                    logger.error(f"Error Tavily (status {response.status_code}): {error_detail}")
                    return {
                        "success": False,
                        "error": f"Tavily API error: {response.status_code} - {error_detail}"
                    }
                    
        except httpx.TimeoutException:
            logger.error("Timeout en petición a Tavily")
            return {"success": False, "error": "Timeout de conexión con Tavily"}
        except Exception as e:
            logger.error(f"Excepción en búsqueda Tavily: {e}")
            return {"success": False, "error": str(e)}
    
    @classmethod
    def _format_results(cls, query: str, results: List[Dict], answer: str = "") -> str:
        """Formatea los resultados en texto plano para consumir desde la IA"""
        output_parts = []
        
        if answer:
            output_parts.append(f"🔍 RESUMEN DE BÚSQUEDA: {answer}\n")
        
        if results:
            output_parts.append(f"📌 RESULTADOS PRINCIPALES para '{query}':\n")
            for i, r in enumerate(results, 1):
                title = r.get("title", "Sin título")
                content = r.get("content", "").strip()
                url = r.get("url", "")
                # Limitar snippet a 300 caracteres
                if len(content) > 300:
                    content = content[:300] + "..."
                output_parts.append(
                    f"{i}. **{title}**\n"
                    f"   {content}\n"
                    f"   🔗 Fuente: {url}\n"
                )
        else:
            output_parts.append(f"No se encontraron resultados para '{query}'.")
        
        return "\n".join(output_parts)
    
    @classmethod
    async def is_configured(cls) -> bool:
        """Verifica si Tavily está configurado (API key presente)"""
        return bool(os.getenv("TAVILY_API_KEY"))