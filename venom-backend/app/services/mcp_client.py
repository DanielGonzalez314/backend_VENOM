# app/services/mcp_client.py
import os
import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Configuración de servidores HTTP MCP (se pueden sobrescribir con variables de entorno)
MCP_FILESYSTEM_URL = os.getenv("MCP_FILESYSTEM_URL", "http://127.0.0.1:8765")
MCP_MUSIC_URL = os.getenv("MCP_MUSIC_URL", "http://127.0.0.1:8766")
MCP_APPS_URL = os.getenv("MCP_APPS_URL", "http://127.0.0.1:8767")
MCP_SYSTEM_URL = os.getenv("MCP_SYSTEM_URL", "http://127.0.0.1:8768")
MCP_WINDOWS_URL = os.getenv("MCP_WINDOWS_URL", "http://host.docker.internal:8769")  # importante

async def execute_mcp_tool(tool_name: str, arguments: Dict[str, Any], server_type: str = "filesystem") -> str:
    """
    Ejecuta una herramienta MCP a través de servidores HTTP.
    Los argumentos deben incluir 'company_id' (obligatorio para music y recomendado para los demás).
    """
    company_id = arguments.get("company_id", "unknown")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # ==================== FILESYSTEM ====================
            if server_type == "filesystem":
                if tool_name == "list_directory":
                    response = await client.get(
                        f"{MCP_FILESYSTEM_URL}/list",
                        params={"path": arguments.get("path", ""), "company_id": company_id}
                    )
                    data = response.json()
                    if data.get("error"):
                        return f"Error: {data['error']}"
                    items = data.get("items", [])
                    if not items:
                        return "El directorio está vacío."
                    return "\n".join([f"📁 {i['name']}" if i['type'] == 'directory' else f"📄 {i['name']} ({i['size']} bytes)" for i in items])
                
                elif tool_name in ["create_directory", "create_file", "delete", "move", "open_explorer", "open_in_explorer"]:
                    endpoint_map = {
                        "create_directory": "/create/directory",
                        "create_file": "/create/file",
                        "delete": "/delete",
                        "move": "/move",
                        "open_explorer": "/open_explorer",
                        "open_in_explorer": "/open_explorer",
                    }
                    endpoint = endpoint_map.get(tool_name)
                    if not endpoint:
                        return f"Herramienta '{tool_name}' no soportada para filesystem"
                    
                    payload = {"company_id": company_id}
                    if tool_name == "create_file":
                        payload.update({
                            "path": arguments.get("path", ""),
                            "content": arguments.get("content", "")
                        })
                    elif tool_name == "move":
                        payload.update({
                            "path": arguments.get("source", ""),
                            "destination": arguments.get("destination", "")
                        })
                    else:
                        payload["path"] = arguments.get("path", "")
                    
                    response = await client.post(f"{MCP_FILESYSTEM_URL}{endpoint}", json=payload)
                    data = response.json()
                    return data.get("message", data.get("error", "Comando ejecutado"))
                
                elif tool_name == "read_file":
                    response = await client.get(
                        f"{MCP_FILESYSTEM_URL}/read",
                        params={"path": arguments.get("path", ""), "company_id": company_id}
                    )
                    data = response.json()
                    if data.get("error"):
                        return f"Error: {data['error']}"
                    return data.get("content", "Archivo vacío")
                
                else:
                    return f"Herramienta '{tool_name}' no soportada para filesystem"

            # ==================== MUSIC ====================
            elif server_type == "music":
                payload = {
                    "action": tool_name,
                    "query": arguments.get("query", ""),
                    "company_id": company_id
                }
                response = await client.post(f"{MCP_MUSIC_URL}/control", json=payload)
                data = response.json()
                if data.get("error"):
                    return f"Error: {data['error']}"
                if tool_name == "status":
                    if data.get("playing"):
                        return f"🎶 Reproduciendo: {data.get('current_song')} - {data.get('queue_length')} canciones en cola"
                    return f"⏸️ Detenido. Última canción: {data.get('current_song') or 'Ninguna'}"
                return data.get("message", "Comando ejecutado")

            # ==================== APPS ====================
            elif server_type == "apps":
                if tool_name == "control_app":
                    response = await client.post(
                        f"{MCP_APPS_URL}/control",
                        json={
                            "app_name": arguments.get("app_name", ""),
                            "action": arguments.get("action", ""),
                            "company_id": company_id
                        }
                    )
                    data = response.json()
                    return data.get("message", data.get("error", "Comando ejecutado"))
                else:
                    return f"Herramienta '{tool_name}' no soportada para apps"

            # ==================== SYSTEM ====================
            elif server_type == "system":
                if tool_name == "get_stats":
                    response = await client.get(f"{MCP_SYSTEM_URL}/stats", params={"company_id": company_id})
                    data = response.json()
                    if data.get("error"):
                        return f"Error: {data['error']}"
                    return (f"🖥️ CPU: {data['cpu_percent']}%\n"
                            f"💾 RAM: {data['memory_percent']}% usado ({data['memory_used']//(1024**3)} GB / {data['memory_total']//(1024**3)} GB)\n"
                            f"💿 Disco: {data['disk_percent']}% usado ({data['disk_used']//(1024**3)} GB / {data['disk_total']//(1024**3)} GB)")
                elif tool_name == "list_processes":
                    response = await client.get(f"{MCP_SYSTEM_URL}/processes", params={"company_id": company_id})
                    data = response.json()
                    if data.get("error"):
                        return f"Error: {data['error']}"
                    procs = data.get("processes", [])
                    if not procs:
                        return "No se encontraron procesos."
                    return "\n".join([f"{p['pid']}: {p['name']} (CPU: {p.get('cpu_percent',0)}%, RAM: {p.get('memory_percent',0)}%)" for p in procs[:20]])
                else:
                    return f"Herramienta '{tool_name}' no soportada para system"

            # ==================== WINDOWS ====================
            elif server_type == "windows":
                if tool_name == "control_window":
                    response = await client.post(
                        f"{MCP_WINDOWS_URL}/window",
                        json={
                            "title": arguments.get("title", ""),
                            "action": arguments.get("action", ""),
                            "company_id": company_id
                        }
                    )
                    data = response.json()
                    return data.get("message", data.get("error", "Comando ejecutado"))
                else:
                    return f"Herramienta '{tool_name}' no soportada para windows"

            else:
                return f"Tipo de servidor '{server_type}' desconocido"
                
    except httpx.ConnectError:
        return f"Error: No se pudo conectar al servidor MCP de tipo '{server_type}'. ¿Está ejecutándose?"
    except Exception as e:
        logger.error(f"Error ejecutando MCP: {e}")
        return f"Error: {e}"