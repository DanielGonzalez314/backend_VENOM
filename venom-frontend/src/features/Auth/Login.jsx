import { useState } from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

// ... (Tus importaciones se mantienen igual)

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null); // Estado para feedback visual de error
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await login(email, password);
      navigate('/'); 
    } catch (err) {
      console.error("Login Error:", err);
      // Capturamos el mensaje del backend o mostramos uno genérico
      const msg = err.response?.data?.detail || "Error de comunicación con Venom.";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#050505] relative overflow-hidden">
      {/* ... Fondos decorativos ... */}

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="z-10 w-full max-w-md p-8 rounded-3xl bg-white/[0.03] border border-white/10 backdrop-blur-xl shadow-2xl"
      >
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-tr from-purple-600 to-blue-600 rounded-2xl mx-auto mb-4 flex items-center justify-center text-3xl font-black text-white shadow-[0_0_20px_rgba(147,51,234,0.3)]">
            V
          </div>
          <h1 className="text-3xl font-bold tracking-tighter text-white">Venom Intelligence</h1>
          <p className="text-gray-500 text-sm mt-2">Protocolo de sincronización neuronal</p>
        </div>

        {/* Alerta de Error */}
        {error && (
          <motion.div 
            initial={{ opacity: 0, x: -10 }} 
            animate={{ opacity: 1, x: 0 }}
            className="mb-6 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs text-center font-bold uppercase tracking-widest"
          >
            {error}
          </motion.div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="text-[10px] font-black text-gray-400 uppercase ml-1 tracking-widest">Email Corporativo</label>
            <input 
              type="email" 
              required
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 mt-1 text-white focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all placeholder:text-gray-700"
              placeholder="id@venom.core"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          
          <div>
            <label className="text-[10px] font-black text-gray-400 uppercase ml-1 tracking-widest">Contraseña</label>
            <input 
              type="password" 
              required
              className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 mt-1 text-white focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all placeholder:text-gray-700"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <motion.button 
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            disabled={isLoading}
            type="submit"
            className={`w-full py-4 font-black rounded-xl transition-all shadow-lg ${
              isLoading 
              ? 'bg-gray-800 text-gray-500 cursor-not-allowed' 
              : 'bg-white text-black hover:bg-purple-50 hover:shadow-purple-500/10'
            }`}
          >
            {isLoading ? 'ESTABLECIENDO ENLACE...' : 'CONECTAR'}
          </motion.button>
        </form>

        <div className="mt-8 pt-6 border-t border-white/5 text-center">
          <p className="text-sm text-gray-500">
            ¿Nueva entidad?{' '}
            <Link to="/register" className="text-white hover:text-purple-400 font-bold transition-colors underline underline-offset-4 decoration-purple-500/50">
              Crear cuenta
            </Link>
          </p>
          <p className="text-[9px] text-gray-600 mt-6 uppercase tracking-[0.2em] font-medium">
            Venom OS v2.1 // Secure Node Access
          </p>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;