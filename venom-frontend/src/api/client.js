import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

// --- INTERCEPTOR DE PETICIÓN ---
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  const savedUser = localStorage.getItem('user_data'); 

  // 1. Inyectar Token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // 2. Inyectar Identidad de Empresa
  if (savedUser) {
    try {
      const user = JSON.parse(savedUser);
      if (user?.company_id) {
        config.headers['X-Company-ID'] = user.company_id;
      }
    } catch (e) {
      console.error("Error en cabecera de compañía:", e);
    }
  }

  return config;
}, (error) => Promise.reject(error));

// --- INTERCEPTOR DE RESPUESTA ---
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Si es 401 y no es una petición de login o refresh
    if (
      error.response?.status === 401 && 
      !originalRequest._retry && 
      !originalRequest.url.includes('/login') &&
      !originalRequest.url.includes('/refresh')
    ) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refreshToken');
      
      if (!refreshToken) {
        handleSessionExpired();
        return Promise.reject(error);
      }

      try {
        // Usamos axios puro para el refresh para evitar que use este mismo interceptor
        const { data } = await axios.post('http://localhost:8000/api/refresh', { 
          refresh_token: refreshToken 
        });

        localStorage.setItem('token', data.access_token);
        
        // Actualizamos la petición original
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        
        // Importante: Volver a ejecutar la petición original con el nuevo token
        return api(originalRequest);
      } catch (refreshError) {
        console.error("Refresh token inválido o expirado");
        handleSessionExpired();
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

// Limpieza total del sistema
const handleSessionExpired = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('user_data');
  
  // Evitar redirección infinita si ya estamos en el login
  if (!window.location.pathname.includes('/login')) {
    window.location.href = '/login';
  }
};

export default api;