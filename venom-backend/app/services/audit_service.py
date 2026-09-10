import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("AuditService")

class AuditService:
    """Detecta información sensible en conversaciones"""
    
    # Patrones de detección (expresiones regulares)
    PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "tarjeta_credito": r'\b(?:\d[ -]*?){13,16}\b',
        "telefono": r'\b(?:\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b',
        "ip_address": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        "url": r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+',
        "password": r'\b(contraseña|password|clave)\s*[=:]\s*\S+',
        "documento_nacional": r'\b\d{8}[A-Za-z]\b'  # ejemplo para DNI español
    }
    
    PALABRAS_RIESGO = [
        "me robaron", "fraude", "ilegal", "amenaza", "secuestro", "violencia",
        "contraseña", "pin", "tarjeta", "credito", "cvv", "vulnerabilidad"
    ]
    
    @staticmethod
    async def audit_conversation(messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Analiza una lista de mensajes (cada uno con role y content) en busca de datos sensibles.
        
        Args:
            messages: Lista de diccionarios [{"role": "user/assistant", "content": "texto"}]
        
        Returns:
            Dict con hallazgos, nivel de riesgo y recomendaciones
        """
        findings = []
        risk_score = 0
        
        for idx, msg in enumerate(messages):
            content = msg.get("content", "")
            role = msg.get("role", "unknown")
            
            for pattern_name, pattern in AuditService.PATTERNS.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    findings.append({
                        "message_index": idx,
                        "role": role,
                        "pattern": pattern_name,
                        "match": match[:50],  # truncar por seguridad
                        "snippet": content[:200] + "..." if len(content) > 200 else content
                    })
                    risk_score += 1
            
            # Palabras de riesgo
            lower_content = content.lower()
            for word in AuditService.PALABRAS_RIESGO:
                if word in lower_content:
                    findings.append({
                        "message_index": idx,
                        "role": role,
                        "pattern": "palabra_riesgo",
                        "match": word,
                        "snippet": content[:200]
                    })
                    risk_score += 0.5
        
        # Nivel de riesgo
        if risk_score == 0:
            risk_level = "bajo"
            recommendation = "No se detectaron datos sensibles ni lenguaje de riesgo."
        elif risk_score < 3:
            risk_level = "medio"
            recommendation = "Se detectaron elementos que merecen revisión humana."
        else:
            risk_level = "alto"
            recommendation = "Se detectaron múltiples datos sensibles. Revise inmediatamente."
        
        return {
            "success": True,
            "risk_level": risk_level,
            "risk_score": round(risk_score, 1),
            "findings_count": len(findings),
            "findings": findings[:20],  # limitar para no saturar
            "recommendation": recommendation,
            "audit_date": datetime.now().isoformat()
        }
    
    @staticmethod
    async def redact_sensitive(text: str) -> str:
        """Reemplaza datos sensibles por [REDACTADO] (útil para logging)"""
        for pattern in AuditService.PATTERNS.values():
            text = re.sub(pattern, "[REDACTADO]", text, flags=re.IGNORECASE)
        return text