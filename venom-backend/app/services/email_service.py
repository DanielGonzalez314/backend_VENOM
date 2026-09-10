# app/services/email_service.py
import os
import logging
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger("EmailService")

class EmailService:
    """
    Servicio para envío de correos electrónicos usando SendGrid.
    Requiere SENDGRID_API_KEY en el archivo .env
    """
    
    SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"
    
    @classmethod
    async def send_email(
        cls,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        from_name: str = "VENOM AI",
        reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envía un correo electrónico usando la API de SendGrid.
        
        Args:
            to: Destinatario (email)
            subject: Asunto del mensaje
            body: Cuerpo en texto plano
            from_email: Email del remitente (opcional, usa SENDGRID_FROM_EMAIL si no se da)
            from_name: Nombre visible del remitente
            reply_to: Dirección para respuestas (opcional)
            
        Returns:
            dict con "success" (bool) y "message" (str)
        """
        # Validar API key
        api_key = os.getenv("SENDGRID_API_KEY")
        if not api_key:
            return {
                "success": False,
                "message": "SendGrid no está configurado. Agrega SENDGRID_API_KEY en el archivo .env"
            }
        
        # Validar email destino
        if not to or "@" not in to:
            return {"success": False, "message": f"Dirección de email inválida: {to}"}
        
        # Email remitente: propio o el de variable de entorno
        from_addr = from_email or os.getenv("SENDGRID_FROM_EMAIL")
        if not from_addr:
            return {
                "success": False,
                "message": "No se ha configurado el email remitente. Define SENDGRID_FROM_EMAIL en .env"
            }
        
        # Construir payload JSON para SendGrid
        payload = {
            "personalizations": [
                {
                    "to": [{"email": to}],
                    "subject": subject
                }
            ],
            "from": {"email": from_addr, "name": from_name},
            "content": [
                {
                    "type": "text/plain",
                    "value": body
                }
            ]
        }
        
        # Opcional: reply-to
        if reply_to:
            payload["reply_to"] = {"email": reply_to}
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    cls.SENDGRID_API_URL,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 202:
                    logger.info(f"✅ Correo enviado exitosamente a {to} | Asunto: {subject}")
                    return {"success": True, "message": f"Correo enviado a {to}"}
                else:
                    # Intentar obtener mensaje de error de SendGrid
                    error_detail = ""
                    try:
                        error_data = response.json()
                        error_detail = error_data.get("errors", [{}])[0].get("message", str(error_data))
                    except:
                        error_detail = response.text
                    
                    logger.error(f"Error SendGrid (status {response.status_code}): {error_detail}")
                    return {
                        "success": False,
                        "message": f"SendGrid rechazó el envío: {error_detail}"
                    }
                    
        except httpx.TimeoutException:
            logger.error("Timeout al conectar con SendGrid")
            return {"success": False, "message": "Timeout de conexión con SendGrid"}
        except Exception as e:
            logger.error(f"Excepción enviando correo: {e}")
            return {"success": False, "message": f"Error interno: {str(e)}"}
    
    @classmethod
    async def send_bulk_emails(
        cls,
        recipients: List[str],
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        from_name: str = "VENOM AI"
    ) -> Dict[str, Any]:
        """
        Envía el mismo correo a múltiples destinatarios (máximo 10 por política de VENOM).
        """
        if len(recipients) > 10:
            return {
                "success": False,
                "message": "Límite de 10 destinatarios por envío (evitar spam)"
            }
        
        results = []
        for recipient in recipients:
            result = await cls.send_email(recipient, subject, body, from_email, from_name)
            results.append(result)
        
        success_count = sum(1 for r in results if r["success"])
        return {
            "success": success_count > 0,
            "message": f"Enviados {len(results)} correos. Éxitos: {success_count}",
            "details": results
        }
    
    @classmethod
    async def send_html_email(
        cls,
        to: str,
        subject: str,
        html_body: str,
        plain_text_body: str = "",
        from_email: Optional[str] = None,
        from_name: str = "VENOM AI"
    ) -> Dict[str, Any]:
        """
        Envía un correo con contenido HTML (además de texto plano opcional).
        """
        api_key = os.getenv("SENDGRID_API_KEY")
        if not api_key:
            return {"success": False, "message": "SendGrid no configurado"}
        
        from_addr = from_email or os.getenv("SENDGRID_FROM_EMAIL")
        if not from_addr:
            return {"success": False, "message": "Falta SENDGRID_FROM_EMAIL"}
        
        payload = {
            "personalizations": [{"to": [{"email": to}], "subject": subject}],
            "from": {"email": from_addr, "name": from_name},
            "content": [
                {"type": "text/plain", "value": plain_text_body or html_body},
                {"type": "text/html", "value": html_body}
            ]
        }
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(cls.SENDGRID_API_URL, headers=headers, json=payload)
                if resp.status_code == 202:
                    return {"success": True, "message": f"HTML email enviado a {to}"}
                else:
                    return {"success": False, "message": f"Error SendGrid: {resp.text}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    @classmethod
    async def is_configured(cls) -> bool:
        """Verifica si SendGrid está configurado (API key y email remitente)"""
        return bool(os.getenv("SENDGRID_API_KEY") and os.getenv("SENDGRID_FROM_EMAIL"))