import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  MusicalNoteIcon, 
  PlayIcon, 
  PauseIcon, 
  StopIcon, 
  ForwardIcon,
  PlusCircleIcon
} from '@heroicons/react/24/solid';
import api from '../api/client';

const MusicBubble = ({ isActive }) => {
  const [expanded, setExpanded] = useState(false);
  const [status, setStatus] = useState({ message: "Inactivo", playing: false });
  const [currentSong, setCurrentSong] = useState("");
  const [queueLength, setQueueLength] = useState(0);
  const [loading, setLoading] = useState(false);
  const intervalRef = useRef(null);

  const fetchStatus = async () => {
    if (!isActive) return;
    try {
      const res = await api.get('/mcp/music/status');
      if (res.data && res.data.message) {
        const msg = res.data.message;
        setStatus({ message: msg, playing: msg.toLowerCase().includes('reproduciendo') });
        // Extraer nombre de la canción (simple)
        if (msg.includes('Reproduciendo:')) {
          setCurrentSong(msg.split('Reproduciendo:')[1].trim());
        } else if (msg.includes('🎶')) {
          setCurrentSong(msg.replace('🎶', '').trim());
        } else {
          setCurrentSong("");
        }
        // Extraer número de cola (opcional)
        const queueMatch = msg.match(/(\d+) canciones en cola/);
        if (queueMatch) setQueueLength(parseInt(queueMatch[1]));
        else setQueueLength(0);
      }
    } catch (err) {
      console.error("Error fetching music status", err);
    }
  };

  useEffect(() => {
    if (isActive) {
      fetchStatus();
      intervalRef.current = setInterval(fetchStatus, 3000);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
      setExpanded(false);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isActive]);

  const sendControl = async (action, query = null) => {
    setLoading(true);
    try {
      const payload = { action };
      if (query) payload.query = query;
      await api.post('/mcp/music/control', payload);
      await fetchStatus(); // refrescar inmediatamente
    } catch (err) {
      console.error(`Error ${action}:`, err);
    } finally {
      setLoading(false);
    }
  };

  const handlePlay = () => {
    const song = prompt("¿Qué canción quieres reproducir? (nombre o URL de YouTube)");
    if (song) sendControl("play_song", song);
  };

  const handleAddToQueue = () => {
    const song = prompt("Canción para añadir a la cola:");
    if (song) sendControl("add_to_queue", song);
  };

  if (!isActive) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0, opacity: 0 }}
        className="fixed bottom-6 right-6 z-50"
      >
        <div
          className={`bg-black/80 backdrop-blur-lg border border-white/10 rounded-full shadow-2xl transition-all duration-300 ${
            expanded ? 'w-80 p-4' : 'w-12 h-12'
          }`}
        >
          {!expanded ? (
            <button
              onClick={() => setExpanded(true)}
              className="w-full h-full flex items-center justify-center text-purple-400 hover:text-purple-300 transition-colors"
            >
              <MusicalNoteIcon className="w-6 h-6" />
            </button>
          ) : (
            <div className="text-white">
              <div className="flex justify-between items-center mb-3">
                <div className="flex items-center gap-2">
                  <MusicalNoteIcon className="w-5 h-5 text-purple-400" />
                  <span className="text-xs font-bold uppercase tracking-wider">Venom Music</span>
                </div>
                <button onClick={() => setExpanded(false)} className="text-gray-400 hover:text-white text-xs">
                  ✕
                </button>
              </div>
              <div className="mb-3">
                <p className="text-xs text-gray-400 truncate">
                  {currentSong || (status.message === "No hay música reproduciéndose." ? "Sin música" : status.message)}
                </p>
                {queueLength > 0 && (
                  <p className="text-[10px] text-cyan-400 mt-1">Cola: {queueLength} canciones</p>
                )}
              </div>
              <div className="flex items-center justify-between gap-2">
                <button
                  onClick={() => sendControl("pause_music")}
                  disabled={loading}
                  className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors disabled:opacity-50"
                  title="Pausar"
                >
                  <PauseIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => sendControl("resume_music")}
                  disabled={loading}
                  className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors disabled:opacity-50"
                  title="Reanudar"
                >
                  <PlayIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => sendControl("next_song")}
                  disabled={loading}
                  className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors disabled:opacity-50"
                  title="Siguiente"
                >
                  <ForwardIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={() => sendControl("stop_music")}
                  disabled={loading}
                  className="p-2 rounded-full bg-white/10 hover:bg-white/20 transition-colors disabled:opacity-50"
                  title="Detener"
                >
                  <StopIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={handlePlay}
                  disabled={loading}
                  className="p-2 rounded-full bg-purple-600 hover:bg-purple-700 transition-colors disabled:opacity-50"
                  title="Reproducir canción"
                >
                  <PlayIcon className="w-4 h-4" />
                </button>
                <button
                  onClick={handleAddToQueue}
                  disabled={loading}
                  className="p-2 rounded-full bg-cyan-600 hover:bg-cyan-700 transition-colors disabled:opacity-50"
                  title="Añadir a cola"
                >
                  <PlusCircleIcon className="w-4 h-4" />
                </button>
              </div>
              <p className="text-[9px] text-gray-500 text-center mt-3">
                MCP activo • control total
              </p>
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default MusicBubble;