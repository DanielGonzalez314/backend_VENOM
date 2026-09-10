import win32gui
import win32con
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import logging

logger = logging.getLogger("MCP_Windows_Server")
app = FastAPI(title="MCP Windows Server")
# este servicio se tiene que ejecutar aparte debido a incompatibilidad de librerias con docker que maneja linux
class WindowControl(BaseModel):
    action: str
    title: str
    company_id: str = "unknown"

def find_window_by_title(partial_title):
    """Busca ventana que contenga el texto parcial (case-insensitive)"""
    def enum_callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            window_text = win32gui.GetWindowText(hwnd)
            if partial_title.lower() in window_text.lower():
                windows.append((hwnd, window_text))
    windows = []
    win32gui.EnumWindows(enum_callback, windows)
    return windows[0] if windows else (None, None)

@app.post("/window")
async def control_window(control: WindowControl):
    try:
        hwnd, exact_title = find_window_by_title(control.title)
        if not hwnd:
            return {"error": f"No se encontró ventana con título que contenga '{control.title}'"}
        
        if control.action == "minimize":
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            msg = f"Ventana '{exact_title}' minimizada."
        elif control.action == "maximize":
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            msg = f"Ventana '{exact_title}' maximizada."
        elif control.action == "close":
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            msg = f"Solicitado cierre de ventana '{exact_title}'."
        elif control.action == "focus":
            win32gui.SetForegroundWindow(hwnd)
            msg = f"Ventana '{exact_title}' enfocada."
        else:
            return {"error": f"Acción '{control.action}' no soportada"}
        
        logger.info(f"✅ {msg} (compañía: {control.company_id})")
        return {"success": True, "message": msg}
    except Exception as e:
        logger.error(f"Error control ventana: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8769, log_level="info")