import subprocess
import psutil
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="MCP Apps Server")

class AppControl(BaseModel):
    action: str  # start, kill
    app_name: str
    company_id: str = "unknown"

@app.post("/control")
async def control_app(control: AppControl):
    try:
        if control.action == "start":
            subprocess.Popen(control.app_name, shell=True)
            return {"success": True, "message": f"Aplicación '{control.app_name}' iniciada."}
        elif control.action == "kill":
            killed = False
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and control.app_name.lower() in proc.info['name'].lower():
                        proc.terminate()
                        killed = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            if killed:
                return {"success": True, "message": f"Proceso(s) '{control.app_name}' terminado(s)."}
            else:
                return {"success": False, "message": f"No se encontró el proceso '{control.app_name}'."}
        else:
            return {"error": "Acción no soportada"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8767, log_level="info")