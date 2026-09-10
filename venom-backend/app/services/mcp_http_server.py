# app/services/mcp_http_server.py
import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCP_FS_Server")

app = FastAPI(title="VENOM MCP Filesystem Server")

class FileOperation(BaseModel):
    path: str
    destination: Optional[str] = None
    content: Optional[str] = None
    company_id: Optional[str] = "unknown"

SPECIAL_PATHS = {
    "documents": Path.home() / "Documents",
    "desktop": Path.home() / "Desktop",
    "downloads": Path.home() / "Downloads",
    "home": Path.home(),
    "users": Path("C:/Users"),
    "program files": Path("C:/Program Files"),
    "program files (x86)": Path("C:/Program Files (x86)"),
    "windows": Path("C:/Windows"),
}

def resolve_path(user_path: str) -> Path:
    if not user_path or user_path.strip() == "":
        return Path.home()
    normalized = user_path.strip().lower()
    for key, path in SPECIAL_PATHS.items():
        if normalized == key or normalized == key.replace(" ", ""):
            return path
    try:
        return Path(user_path).expanduser().resolve()
    except Exception:
        return Path(user_path)

def log_operation(company_id: str, action: str, path: str, extra: str = ""):
    logger.info(f"📁 [{company_id}] {action}: {path} {extra}")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/list")
async def list_directory(path: str = "", company_id: str = "unknown"):
    try:
        target = resolve_path(path)
        if not target.exists():
            return {"error": f"El directorio '{path}' no existe."}
        if not target.is_dir():
            return {"error": f"'{path}' no es un directorio."}
        items = []
        for item in target.iterdir():
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0,
                "modified": item.stat().st_mtime
            })
        log_operation(company_id, "LIST_DIR", str(target))
        return {"success": True, "items": items, "path": str(target)}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"error": str(e)}

@app.post("/create/directory")
async def create_directory(data: FileOperation):
    try:
        target = resolve_path(data.path)
        if target.exists():
            return {"error": f"El directorio '{data.path}' ya existe."}
        target.mkdir(parents=True)
        log_operation(data.company_id, "CREATE_DIR", str(target))
        return {"success": True, "message": f"Directorio '{data.path}' creado."}
    except Exception as e:
        return {"error": str(e)}

@app.post("/create/file")
async def create_file(data: FileOperation):
    try:
        target = resolve_path(data.path)
        if target.exists():
            return {"error": f"El archivo '{data.path}' ya existe."}
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data.content or "", encoding="utf-8")
        log_operation(data.company_id, "CREATE_FILE", str(target))
        return {"success": True, "message": f"Archivo '{data.path}' creado."}
    except Exception as e:
        return {"error": str(e)}

@app.get("/read")
async def read_file(path: str, company_id: str = "unknown"):
    try:
        target = resolve_path(path)
        if not target.exists():
            return {"error": f"El archivo '{path}' no existe."}
        if not target.is_file():
            return {"error": f"'{path}' no es un archivo."}
        content = target.read_text(encoding="utf-8")
        log_operation(company_id, "READ_FILE", str(target))
        return {"success": True, "content": content[:10000]}
    except Exception as e:
        return {"error": str(e)}

@app.post("/delete")
async def delete_file_or_directory(data: FileOperation):
    try:
        target = resolve_path(data.path)
        if not target.exists():
            return {"error": f"La ruta '{data.path}' no existe."}
        if target.is_file():
            target.unlink()
        else:
            shutil.rmtree(target)
        log_operation(data.company_id, "DELETE", str(target))
        return {"success": True, "message": f"Eliminado: '{data.path}'"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/move")
async def move_file(data: FileOperation):
    try:
        src = resolve_path(data.path)
        dst = resolve_path(data.destination)
        if not src.exists():
            return {"error": f"El origen '{data.path}' no existe."}
        if dst.exists():
            return {"error": f"El destino '{data.destination}' ya existe."}
        shutil.move(str(src), str(dst))
        log_operation(data.company_id, "MOVE", f"{src} -> {dst}")
        return {"success": True, "message": f"Movido de '{data.path}' a '{data.destination}'."}
    except Exception as e:
        return {"error": str(e)}

@app.post("/open_explorer")
async def open_in_explorer(path: str = "", company_id: str = "unknown"):
    """Abre el Explorador de Windows con cmd /c start (método más fiable)."""
    try:
        target = resolve_path(path) if path else Path.home()
        if not target.exists():
            return {"error": f"La ruta '{path}' no existe."}
        path_str = str(target)
        # cmd /c start "" "ruta"  --> abre la carpeta en una nueva ventana
        cmd = f'cmd /c start "" "{path_str}"'
        subprocess.Popen(cmd, shell=True)
        log_operation(company_id, "OPEN_EXPLORER", path_str, "cmd start")
        return {"success": True, "message": f"Explorador abierto en {target}"}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"error": str(e)}

@app.post("/open")
async def open_legacy(path: str = "", company_id: str = "unknown"):
    return await open_in_explorer(path, company_id)

@app.get("/disk_usage")
async def disk_usage(path: str = "", company_id: str = "unknown"):
    try:
        target = resolve_path(path) if path else Path.cwd()
        usage = shutil.disk_usage(target)
        return {
            "success": True,
            "total_gb": usage.total // (1024**3),
            "used_gb": usage.used // (1024**3),
            "free_gb": usage.free // (1024**3),
            "percent_used": round((usage.used / usage.total) * 100, 2)
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/file_info")
async def file_info(path: str, company_id: str = "unknown"):
    try:
        target = resolve_path(path)
        stat = target.stat()
        return {
            "success": True,
            "name": target.name,
            "type": "directory" if target.is_dir() else "file",
            "size_bytes": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("MCP_FILESYSTEM_PORT", "8765"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")