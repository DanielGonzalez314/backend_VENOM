import { createContext, useContext, useState, useEffect } from 'react';
// AJUSTE DE RUTA: Subimos un nivel (..) para salir de 'context' y entramos en 'api'
import api from '../api/client';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = () => {
      // Sincronizado con client.js
      const token = localStorage.getItem('token');
      const savedUser = localStorage.getItem('user_data');
      
      if (token && savedUser) {
        try {
          setUser(JSON.parse(savedUser));
        } catch (err) {
          console.error("Error restaurando sesión:", err);
          logout(); 
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, []);

  const login = async (email, password) => {
    const params = new URLSearchParams();
    params.append('username', email); 
    params.append('password', password);

    try {
      const { data } = await api.post('/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });

      // LLAVES ESTÁNDAR PARA EL INTERCEPTOR
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('refreshToken', data.refresh_token);
      
      const userData = { 
        ...data.user,
        loggedIn: true 
      };
      
      localStorage.setItem('user_data', JSON.stringify(userData));
      setUser(userData); 
      
      return data;
    } catch (error) {
      console.error("Fallo en la autenticación:", error);
      throw error;
    }
  };

  const registerCompany = async (formData) => {
    try {
      const { data } = await api.post('/register', formData);
      return data;
    } catch (err) {
      console.error("Error en el registro:", err);
      throw err; 
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user_data');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      login, 
      register: registerCompany, 
      logout, 
      loading 
    }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth debe usarse dentro de un AuthProvider");
  }
  return context;
};