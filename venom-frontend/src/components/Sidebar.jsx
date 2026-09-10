import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  ChatBubbleLeftRightIcon, 
  Square3Stack3DIcon, 
  PlusIcon,
  ArrowLeftOnRectangleIcon,
  EllipsisVerticalIcon,
  TrashIcon,
  CircleStackIcon,
  CpuChipIcon
} from '@heroicons/react/24/outline';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

const Sidebar = ({ onSelectConversation, currentConversationId }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showUserPanel, setShowUserPanel] = useState(false);
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const activeTab = location.pathname.includes('/knowledge') ? 'knowledge' : 'chat';

  // 1. CARGA DE HISTORIAL (Optimizado con manejo de caché local opcional)
  const fetchHistory = useCallback(async () => {
    try {
      setLoading(true);
      const { data } = await api.get('/conversations');
      setHistory(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Error cargando historial de Venom", err);
      setHistory([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [currentConversationId, fetchHistory]); 

  // 2. NAVEGACIÓN
  const handleTabChange = (tab) => {
    if (tab === 'chat') {
      navigate('/');
    } else {
      navigate('/knowledge');
    }
    setShowUserPanel(false);
  };

  const handleNewChat = () => {
    onSelectConversation('new');
    if (location.pathname !== '/') navigate('/');
    setShowUserPanel(false);
  };

  const deleteConversation = async (id, e) => {
    e.stopPropagation(); 
    if (!window.confirm("¿Deseas purgar esta sesión permanentemente?")) return;
    
    try {
      await api.delete(`/conversations/${id}`);
      setHistory(prev => prev.filter(c => c.id !== id));
      if (currentConversationId === id) {
        onSelectConversation('new');
      }
    } catch (err) {
      console.error("Fallo al eliminar registro", err);
    }
  };

  return (
    <div className="flex flex-col h-full p-4 bg-[#050505] text-gray-100 relative select-none border-r border-white/5">
      
      {/* BRANDING: Efecto Neon Deep */}
      <div 
        className="flex items-center gap-3 mb-10 px-2 cursor-pointer group" 
        onClick={handleNewChat}
      >
        <div className="relative">
          <div className="absolute inset-0 bg-purple-600 blur-[12px] opacity-20 group-hover:opacity-60 transition-opacity" />
          <div className="relative w-10 h-10 bg-gradient-to-tr from-purple-600 via-indigo-700 to-black rounded-xl flex items-center justify-center border border-white/10 shadow-2xl transform group-hover:scale-105 transition-all">
            <CpuChipIcon className="w-6 h-6 text-white" />
          </div>
        </div>
        <div className="flex flex-col">
          <span className="font-black tracking-[0.25em] text-xl leading-none text-white uppercase italic">Venom</span>
          <span className="text-[7px] text-purple-500 font-black tracking-[0.4em] mt-1.5 opacity-70">NEURAL_INTERFACE_V3</span>
        </div>
      </div>

      {/* NAVEGACIÓN PRINCIPAL: Botones Estilo Industrial */}
      <nav className="space-y-1.5 mb-10">
        <button 
          onClick={() => handleTabChange('chat')}
          className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all border ${
            activeTab === 'chat' 
            ? 'bg-purple-600/10 border-purple-500/40 text-white shadow-[0_0_15px_rgba(168,85,247,0.1)]' 
            : 'border-transparent text-gray-500 hover:bg-white/[0.03] hover:text-gray-300'
          }`}
        >
          <ChatBubbleLeftRightIcon className={`w-5 h-5 ${activeTab === 'chat' ? 'text-purple-400' : ''}`} />
          <span className="font-bold text-[10px] uppercase tracking-[0.2em]">Chat Lab</span>
        </button>
        
        <button 
          onClick={() => handleTabChange('knowledge')}
          className={`w-full flex items-center gap-3 p-3 rounded-xl transition-all border ${
            activeTab === 'knowledge' 
            ? 'bg-purple-600/10 border-purple-500/40 text-white shadow-[0_0_15px_rgba(168,85,247,0.1)]' 
            : 'border-transparent text-gray-500 hover:bg-white/[0.03] hover:text-gray-300'
          }`}
        >
          <Square3Stack3DIcon className={`w-5 h-5 ${activeTab === 'knowledge' ? 'text-purple-400' : ''}`} />
          <span className="font-bold text-[10px] uppercase tracking-[0.2em]">Knowledge</span>
        </button>
      </nav>

      {/* HISTORIAL: Scroll Personalizado */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex items-center justify-between mb-4 px-2 opacity-50">
          <div className="flex items-center gap-2">
            <CircleStackIcon className="w-3 h-3" />
            <p className="text-[9px] uppercase tracking-[0.3em] font-black">Archive_History</p>
          </div>
          <button 
            onClick={handleNewChat} 
            className="p-1 hover:text-purple-400 transition-colors"
            title="Nuevo Análisis"
          >
            <PlusIcon className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-1 scrollbar-hide hover:scrollbar-default pr-1">
          {loading && history.length === 0 ? (
            <div className="space-y-3 p-2">
              {[1,2,3].map(i => (
                <div key={i} className="h-8 bg-white/[0.02] border border-white/5 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : history.length === 0 ? (
            <div className="text-[9px] text-gray-700 text-center py-10 font-mono uppercase tracking-widest">
              No_Records_Found
            </div>
          ) : (
            <AnimatePresence mode='popLayout'>
              {history.map((chat) => (
                <motion.div
                  key={chat.id}
                  layout
                  initial={{ opacity: 0, x: -5 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  onClick={() => {
                    handleTabChange('chat');
                    onSelectConversation(chat.id);
                  }}
                  className={`group flex items-center justify-between p-3 rounded-xl cursor-pointer text-[11px] transition-all border ${
                    currentConversationId === chat.id 
                    ? 'bg-white/[0.07] border-white/10 text-white' 
                    : 'border-transparent text-gray-500 hover:bg-white/[0.02] hover:text-gray-300'
                  }`}
                >
                  <span className="truncate flex-1 pr-2 font-mono tracking-tighter lowercase">
                    {chat.title || "null_session"}
                  </span>
                  <button 
                    onClick={(e) => deleteConversation(chat.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-500 transition-all transform hover:scale-110"
                  >
                    <TrashIcon className="w-3.5 h-3.5" />
                  </button>
                </motion.div>
              ))}
            </AnimatePresence>
          )}
        </div>
      </div>

      {/* PANEL DE USUARIO: Glassmorphism */}
      <div className="pt-4 border-t border-white/5 relative mt-auto">
        <AnimatePresence>
          {showUserPanel && (
            <motion.div 
              initial={{ opacity: 0, y: 10 }} 
              animate={{ opacity: 1, y: 0 }} 
              exit={{ opacity: 0, y: 10 }}
              className="absolute bottom-20 left-0 right-0 bg-[#0d0d0d]/95 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-2xl overflow-hidden z-[100] mx-2"
            >
              <div className="px-4 py-3 border-b border-white/5">
                <p className="text-[7px] text-green-500 font-black uppercase tracking-[0.2em] mb-1 flex items-center gap-1">
                  <span className="w-1 h-1 bg-green-500 rounded-full animate-ping" />
                  System_Online
                </p>
                <p className="text-[10px] text-gray-400 truncate font-mono">{user?.email}</p>
              </div>
              <button 
                onClick={logout} 
                className="w-full flex items-center gap-3 p-4 text-[10px] text-red-400 hover:bg-red-500/10 transition-colors font-black uppercase tracking-widest"
              >
                <ArrowLeftOnRectangleIcon className="w-4 h-4" />
                Terminal_Exit
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        <button 
          onClick={() => setShowUserPanel(!showUserPanel)}
          className={`w-full flex items-center gap-3 p-3 rounded-2xl transition-all border ${
            showUserPanel ? 'bg-white/5 border-white/10' : 'border-transparent hover:bg-white/[0.03]'
          }`}
        >
          <div className="relative">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex-shrink-0 flex items-center justify-center font-black text-white text-xs shadow-lg border border-white/10">
              {user?.full_name?.charAt(0) || "U"}
            </div>
          </div>
          
          <div className="text-left flex-1 truncate">
            <p className="text-[11px] font-black text-white truncate uppercase tracking-tight">
              {user?.full_name || "Venom_User"}
            </p>
            <p className="text-[8px] text-gray-500 truncate font-mono uppercase">
              {user?.company_name || "Guest_Access"}
            </p>
          </div>
          <EllipsisVerticalIcon className={`w-4 h-4 text-gray-600 transition-transform ${showUserPanel ? 'rotate-90 text-purple-400' : ''}`} />
        </button>
      </div>
    </div>
  );
};

export default Sidebar;