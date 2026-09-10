import { useState, useEffect } from 'react';

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Al cargar el hook, verificamos si hay una sesión guardada
  useEffect(() => {
    const savedUser = localStorage.getItem('venom_user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = (userData) => {
    // userData debe contener: { id, name, company_id, role, token }
    setUser(userData);
    localStorage.setItem('venom_user', JSON.stringify(userData));
    
    // Configurar el header de API globalmente después del login
    // Esto asegura que todas las llamadas futuras lleven el ID de empresa
    import('../api/client').then(module => {
      module.default.defaults.headers.common['X-Company-ID'] = userData.company_id;
    });
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('venom_user');
    // Limpiar headers
    import('../api/client').then(module => {
      delete module.default.defaults.headers.common['X-Company-ID'];
    });
    window.location.href = '/login';
  };

  return {
    user,
    companyId: user?.company_id,
    isAuthenticated: !!user,
    loading,
    login,
    logout
  };
};