import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext'; 

const CompanyRegistry = () => {
  const navigate = useNavigate();
  const { register } = useAuth(); 
  
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    company_name: '', 
    industry: '',
    full_name: '', 
    email: '', 
    password: ''
  });

  // --- Lógica de Validación (Ingeniería de Software) ---
  
  // Paso 1: Entidad (Empresa e Industria obligatorias)
  const isStep1Valid = formData.company_name.trim().length > 0 && formData.industry !== '';
  
  // Paso 2: Avatar (Nombre, Email válido y Password mínima de 6 caracteres)
  const isStep2Valid = 
    formData.full_name.trim().length > 0 && 
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email) && 
    formData.password.length >= 6;

  const handleNext = () => {
    if (isStep1Valid) setStep(2);
  };

  const handleRegister = async () => {
    if (!isStep2Valid) return;

    // Payload exacto según UnifiedRegister schema
    const payload = {
      company_name: formData.company_name.trim(),
      industry: formData.industry,
      full_name: formData.full_name.trim(),
      email: formData.email.trim(),
      password: formData.password
    };

    try {
      await register(payload);
      alert("¡Simbiosis Creada! Identidad verificada en la base de datos.");
      navigate("/login");
    } catch (err) {
      console.error("Fallo de sincronización:", err.response?.data);
      const backendError = err.response?.data?.detail;
      
      // Manejo de errores de integridad (400) o validación (422)
      const message = typeof backendError === 'string' 
        ? backendError 
        : "Error en la matriz: El email o la empresa ya existen.";
      
      alert(message);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center p-4">
      <div className="max-w-md w-full p-8 bg-white/[0.02] border border-white/10 rounded-3xl backdrop-blur-md shadow-2xl">
        
        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex gap-2 mb-4">
            <div className={`h-1 flex-1 rounded-full transition-colors duration-500 ${step >= 1 ? 'bg-purple-600' : 'bg-white/10'}`} />
            <div className={`h-1 flex-1 rounded-full transition-colors duration-500 ${step >= 2 ? 'bg-purple-600' : 'bg-white/10'}`} />
          </div>
          <h2 className="text-2xl font-bold text-white">
            {step === 1 ? "Identifica tu Entidad" : "Crea tu Avatar Admin"}
          </h2>
          <p className="text-white/40 text-sm mt-1">
            {step === 1 ? "Configuración de la empresa para Project Venom" : "Credenciales de acceso maestro"}
          </p>
        </div>

        <AnimatePresence mode="wait">
          {step === 1 ? (
            <motion.div 
              key="step1"
              initial={{ x: 20, opacity: 0 }} 
              animate={{ x: 0, opacity: 1 }} 
              exit={{ x: -20, opacity: 0 }}
              className="space-y-4"
            >
              <div>
                <label className="text-xs text-purple-400 font-mono mb-1 block">COMPANY_ID</label>
                <input 
                  className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white focus:ring-2 focus:ring-purple-600 outline-none transition-all"
                  placeholder="Nombre de la Empresa"
                  value={formData.company_name}
                  onChange={e => setFormData({...formData, company_name: e.target.value})}
                />
              </div>
              
              <div>
                <label className="text-xs text-purple-400 font-mono mb-1 block">INDUSTRY_SECTOR</label>
                <select 
                  className="w-full bg-[#151515] border border-white/10 p-3 rounded-xl text-white outline-none focus:ring-2 focus:ring-purple-600"
                  value={formData.industry}
                  onChange={e => setFormData({...formData, industry: e.target.value})}
                >
                  <option value="">Seleccionar Sector...</option>
                  <option value="tech">Tecnología / Software</option>
                  <option value="legal">Legal / Corporativo</option>
                  <option value="health">Salud / Biotech</option>
                  <option value="retail">Comercio / Logística</option>
                </select>
              </div>

              <button 
                onClick={handleNext}
                disabled={!isStep1Valid}
                className={`w-full py-3 rounded-xl font-bold transition-all duration-300 ${
                  isStep1Valid 
                    ? 'bg-purple-600 text-white hover:bg-purple-700 shadow-lg shadow-purple-900/20' 
                    : 'bg-white/5 text-white/20 cursor-not-allowed'
                }`}
              >
                Continuar
              </button>
            </motion.div>
          ) : (
            <motion.div 
              key="step2"
              initial={{ x: 20, opacity: 0 }} 
              animate={{ x: 0, opacity: 1 }} 
              exit={{ x: -20, opacity: 0 }}
              className="space-y-4"
            >
              <input 
                className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:ring-2 focus:ring-purple-600"
                placeholder="Nombre Completo del Admin"
                value={formData.full_name}
                onChange={e => setFormData({...formData, full_name: e.target.value})}
              />
              <input 
                type="email"
                className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:ring-2 focus:ring-purple-600"
                placeholder="Email Maestro"
                value={formData.email}
                onChange={e => setFormData({...formData, email: e.target.value})}
              />
              <input 
                type="password"
                className="w-full bg-white/5 border border-white/10 p-3 rounded-xl text-white outline-none focus:ring-2 focus:ring-purple-600"
                placeholder="Contraseña (Mín. 6 caracteres)"
                value={formData.password}
                onChange={e => setFormData({...formData, password: e.target.value})}
              />
              
              <div className="flex gap-2">
                <button 
                  onClick={() => setStep(1)} 
                  className="flex-1 py-3 bg-white/5 text-white rounded-xl hover:bg-white/10 transition"
                >
                  Volver
                </button>
                <button 
                  onClick={handleRegister} 
                  disabled={!isStep2Valid}
                  className={`flex-[2] py-3 rounded-xl font-bold transition-all ${
                    isStep2Valid 
                      ? 'bg-white text-black hover:bg-gray-200' 
                      : 'bg-white/5 text-white/20 cursor-not-allowed'
                  }`}
                >
                  Establecer
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default CompanyRegistry;