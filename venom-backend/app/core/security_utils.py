from fastapi import HTTPException, Request
import time
# Diccionario simple en memoria: {user_email: [timestamps]}
user_requests = {}

async def rate_limiter(email: str):
    now = time.time()
    if email not in user_requests:
        user_requests[email] = []
    # Filtrar timestamps de hace más de 60 segundos
    user_requests[email] = [t for t in user_requests[email] if now - t < 60]
    
    if len(user_requests[email]) >= 10:
        raise HTTPException(status_code=429, detail="Límite alcanzado (10/min). Espera un poco.")
    
    user_requests[email].append(now)