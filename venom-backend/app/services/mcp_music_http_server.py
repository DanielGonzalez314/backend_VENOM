import subprocess
import yt_dlp
import os
import shutil
import time
import threading
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="VENOM MCP Music Server (Multi-tenant)")

# Configuración
BASE_DOWNLOAD_DIR = Path("./downloads")
MUSIC_TTL_HOURS = int(os.environ.get("MUSIC_TTL_HOURS", "24"))  # horas para mantener música
CLEANUP_INTERVAL_SECONDS = 3600  # limpiar cada hora

tenant_state = {}

class MusicControl(BaseModel):
    action: str
    query: str = None
    company_id: str   # <--- NUEVO: obligatorio para identificar al tenant

def get_tenant_dir(company_id: str) -> Path:
    """Devuelve el directorio de descargas para un tenant específico."""
    tenant_dir = BASE_DOWNLOAD_DIR / company_id
    tenant_dir.mkdir(parents=True, exist_ok=True)
    return tenant_dir

def get_ydl_opts(company_id: str):
    """Configuración de yt-dlp para descargar en la carpeta del tenant."""
    return {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'outtmpl': str(get_tenant_dir(company_id) / '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }

def get_tenant_state(company_id: str):
    """Obtiene el estado de reproducción para un tenant, creándolo si no existe."""
    if company_id not in tenant_state:
        tenant_state[company_id] = {
            "current_process": None,
            "current_title": "Ninguna",
            "current_file": None,
            "queue": [],
            "queue_index": 0,
            "is_playing": False,
        }
    return tenant_state[company_id]

def play_file(company_id: str, file_path: str, title: str):
    """Reproduce un archivo de audio para un tenant específico."""
    state = get_tenant_state(company_id)
    # Detener reproducción anterior si existe
    if state["current_process"] and state["current_process"].poll() is None:
        state["current_process"].terminate()
        time.sleep(0.5)
    state["current_title"] = title
    state["current_file"] = file_path
    state["current_process"] = subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", file_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    state["is_playing"] = True

def play_next(company_id: str):
    """Reproduce la siguiente canción en la cola del tenant."""
    state = get_tenant_state(company_id)
    if state["queue_index"] < len(state["queue"]):
        next_item = state["queue"][state["queue_index"]]
        state["queue_index"] += 1
        play_file(company_id, next_item['path'], next_item['title'])
        return True
    else:
        state["is_playing"] = False
        return False

def monitor_playback():
    """Monitorea la reproducción de todos los tenants y avanza automáticamente."""
    while True:
        for cid, state in tenant_state.items():
            if state["current_process"] and state["current_process"].poll() is not None:
                # La canción terminó, reproducir siguiente si hay cola
                play_next(cid)
        time.sleep(1)

# Iniciar hilo monitor
threading.Thread(target=monitor_playback, daemon=True).start()

def cleanup_old_music():
    """Elimina archivos de música que superen MUSIC_TTL_HOURS horas."""
    while True:
        now = datetime.now()
        cutoff = now - timedelta(hours=MUSIC_TTL_HOURS)
        for tenant_dir in BASE_DOWNLOAD_DIR.iterdir():
            if tenant_dir.is_dir():
                for file_path in tenant_dir.glob("**/*"):
                    if file_path.is_file():
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if mtime < cutoff:
                            try:
                                file_path.unlink()
                                print(f"🗑️ Eliminado archivo antiguo: {file_path}")
                            except Exception as e:
                                print(f"Error eliminando {file_path}: {e}")
        time.sleep(CLEANUP_INTERVAL_SECONDS)

# Iniciar hilo de limpieza
threading.Thread(target=cleanup_old_music, daemon=True).start()

@app.post("/control")
async def music_control(control: MusicControl):
    """Controla la reproducción de música para un tenant específico."""
    company_id = control.company_id
    state = get_tenant_state(company_id)

    try:
        if control.action == "play_song":
            if not control.query:
                return {"error": "Se requiere 'query' para play_song"}
            # Descargar la canción en la carpeta del tenant
            with yt_dlp.YoutubeDL(get_ydl_opts(company_id)) as ydl:
                info = ydl.extract_info(f"ytsearch1:{control.query}", download=True)['entries'][0]
                file_path = ydl.prepare_filename(info)
                base, _ = os.path.splitext(file_path)
                file_path_mp3 = base + '.mp3'
                if not os.path.exists(file_path_mp3):
                    file_path_mp3 = file_path
                title = info.get('title', control.query)
            # Reemplazar cola y empezar a reproducir
            state["queue"] = [{'path': file_path_mp3, 'title': title}]
            state["queue_index"] = 0
            if state["current_process"] and state["current_process"].poll() is None:
                state["current_process"].terminate()
                await asyncio.sleep(0.5)
            play_file(company_id, file_path_mp3, title)
            return {"success": True, "message": f"Reproduciendo: {title}"}

        elif control.action == "stop_music":
            if state["current_process"] and state["current_process"].poll() is None:
                state["current_process"].terminate()
                state["current_process"] = None
            state["queue"] = []
            state["queue_index"] = 0
            state["is_playing"] = False
            return {"success": True, "message": "Música detenida."}

        elif control.action == "next_song":
            if state["queue_index"] < len(state["queue"]):
                if state["current_process"] and state["current_process"].poll() is None:
                    state["current_process"].terminate()
                    await asyncio.sleep(0.5)
                play_next(company_id)
                return {"success": True, "message": "Siguiente canción."}
            return {"success": False, "message": "No hay más canciones."}

        elif control.action == "add_to_queue":
            if not control.query:
                return {"error": "Se requiere 'query' para add_to_queue"}
            with yt_dlp.YoutubeDL(get_ydl_opts(company_id)) as ydl:
                info = ydl.extract_info(f"ytsearch1:{control.query}", download=True)['entries'][0]
                file_path = ydl.prepare_filename(info)
                base, _ = os.path.splitext(file_path)
                file_path_mp3 = base + '.mp3'
                if not os.path.exists(file_path_mp3):
                    file_path_mp3 = file_path
                title = info.get('title', control.query)
            state["queue"].append({'path': file_path_mp3, 'title': title})
            return {"success": True, "message": f"Añadido a cola: {title} (posición {len(state['queue'])})"}

        elif control.action == "status":
            if state["current_process"] and state["current_process"].poll() is None:
                return {
                    "success": True,
                    "playing": True,
                    "current_song": state["current_title"],
                    "queue_length": len(state["queue"]) - state["queue_index"]
                }
            return {
                "success": True,
                "playing": False,
                "current_song": state["current_title"] if state["current_title"] else "Ninguna",
                "queue_length": len(state["queue"]) - state["queue_index"]
            }

        else:
            return {"error": f"Acción '{control.action}' no soportada"}

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8766, log_level="info")