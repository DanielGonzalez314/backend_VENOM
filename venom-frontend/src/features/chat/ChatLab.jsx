import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import api from '../../api/client'; 
import { 
  PlusCircleIcon, 
  PaperAirplaneIcon, 
  XMarkIcon, 
  SparklesIcon,
  DocumentArrowDownIcon,
  DocumentIcon
} from '@heroicons/react/24/outline';

const ChatLab = ({ conversationId, setConversationId }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [file, setFile] = useState(null);
  const [filePreview, setFilePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);
  const fileInputRef = useRef(null);

  // --- Helper: detectar si un texto contiene un PDF en base64 ---
  const extractPdfFromText = (text) => {
    // Busca una cadena larga que empiece con JVBER (PDF magic number en base64)
    const pdfRegex = /(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?/g;
    const candidates = text.match(pdfRegex) || [];
    for (const candidate of candidates) {
      if (candidate.length > 500 && candidate.startsWith('JVBER')) {
        return candidate;
      }
    }
    return null;
  };

  // --- 1. CARGA DE HISTORIAL ---
  useEffect(() => {
    const loadHistory = async () => {
      if (!conversationId || conversationId === "new" || conversationId === "undefined") {
        setMessages([]);
        return;
      }
      
      try {
        setLoading(true);
        const { data } = await api.get(`/conversations/${conversationId}`);
        setMessages(data?.messages || []);
      } catch (err) {
        console.error("Error al recuperar el historial:", err);
        setMessages([]); 
      } finally {
        setLoading(false);
      }
    };
    loadHistory();
  }, [conversationId]);

  // Manejo de vista previa (imagen o archivo genérico)
  useEffect(() => {
    if (!file) { 
      setFilePreview(null); 
      return; 
    }
    if (file.type.startsWith('image/')) {
      const objectUrl = URL.createObjectURL(file);
      setFilePreview(objectUrl);
      return () => URL.revokeObjectURL(objectUrl);
    } else {
      // Para archivos no imagen, mostrar un icono y el nombre
      setFilePreview({ name: file.name, type: file.type });
    }
  }, [file]);

  // Scroll automático
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading]);

  const scrollToMessage = (index) => {
    const elements = document.querySelectorAll('.message-bubble');
    elements[index]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  // --- Manejo de pegar imágenes desde portapapeles ---
  const handlePaste = (e) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (const item of items) {
      if (item.type.startsWith('image/')) {
        const pastedFile = item.getAsFile();
        setFile(pastedFile);
        break;
      }
    }
  };

  // --- 2. LÓGICA DE ENVÍO ---
  const sendMessage = async () => {
    if (!input.trim() && !file) return;

    const userMessageContent = input;
    const tempUserMsg = { role: 'user', content: userMessageContent };

    setMessages(prev => [...prev, tempUserMsg]);
    setInput("");
    setLoading(true);

    const formData = new FormData();
    formData.append('query', userMessageContent);
    if (file) formData.append('file', file);

    try {
      const activeId = (conversationId && conversationId !== "new") ? conversationId : "new";
      const { data } = await api.post(`/ask/${activeId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      let answerText = data.answer;
      let pdfBase64 = null;

      // Intentar extraer PDF de la respuesta (si existe)
      if (answerText && typeof answerText === 'string') {
        const extracted = extractPdfFromText(answerText);
        if (extracted) {
          pdfBase64 = extracted;
          // Limpiar el texto para que no muestre el base64 gigante
          answerText = answerText.replace(extracted, '').trim();
          if (!answerText) answerText = "✅ **Reporte generado** (puedes descargarlo abajo).";
        }
      }

      // Construir mensaje del asistente con posible adjunto PDF
      const assistantMessage = {
        role: 'assistant',
        content: answerText,
        ...(pdfBase64 && { pdfData: pdfBase64, pdfName: `reporte_${Date.now()}.pdf` })
      };

      setMessages(prev => [...prev, assistantMessage]);

      if (data.is_new && data.conversation_id) {
        setConversationId(data.conversation_id);
      }

    } catch (err) {
      console.error("Error Venom Core:", err);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "❌ **Error de Conexión**: El núcleo Venom no pudo procesar la solicitud.",
        isError: true
      }]);
    } finally {
      setLoading(false);
      setFile(null);
      setFilePreview(null);
    }
  };

  // Función para descargar PDF
  const downloadPdf = (base64Data, filename) => {
    try {
      const byteCharacters = atob(base64Data);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error al descargar PDF:", error);
    }
  };

  return (
    <div className="flex flex-col h-full w-full max-w-5xl mx-auto relative overflow-hidden bg-transparent" onPaste={handlePaste}>
      
      {/* BURBUJAS DE NAVEGACIÓN LATERAL */}
      <div className="absolute left-4 top-10 hidden lg:flex flex-col gap-3 z-20">
        {Array.isArray(messages) && messages.filter(m => m.role === 'user').map((m, i) => (
          <button
            key={i}
            onClick={() => scrollToMessage(messages.indexOf(m))}
            className="w-2.5 h-2.5 rounded-full bg-white/10 hover:bg-purple-500 transition-all group relative border border-white/10"
          >
            <span className="absolute left-6 top-1/2 -translate-y-1/2 scale-0 group-hover:scale-100 transition-transform bg-[#1a1a1a] text-[10px] py-1 px-2 rounded border border-white/10 whitespace-nowrap text-white z-50">
              {m.content.substring(0, 20)}...
            </span>
          </button>
        ))}
      </div>

      {/* ÁREA DE MENSAJES */}
      <div className="flex-1 overflow-y-auto px-4 custom-scrollbar space-y-8 pb-48 pt-10 scroll-smooth text-white">
        {messages.length === 0 && !loading && (
          <div className="h-full flex flex-col items-center justify-center text-center opacity-30 select-none">
            <SparklesIcon className="w-16 h-16 text-purple-600 mb-4 animate-pulse" />
            <h2 className="text-2xl font-black uppercase tracking-[0.3em]">Venom Lab</h2>
            <p className="text-xs text-gray-500 mt-2 font-mono">CORE_SYSTEM_READY // WAITING_INPUT</p>
          </div>
        )}

        <AnimatePresence initial={false}>
          {Array.isArray(messages) && messages.map((m, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex message-bubble ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`p-5 rounded-2xl max-w-[85%] text-sm shadow-2xl ${
                m.role === 'user' 
                  ? 'bg-purple-600 text-white rounded-tr-none' 
                  : m.isError 
                    ? 'bg-red-900/30 border border-red-500/50 text-red-200 rounded-tl-none'
                    : 'bg-[#0d0d0d] border border-white/10 text-gray-200 rounded-tl-none'
              }`}>
                <div className="prose prose-invert prose-sm max-w-none break-words leading-relaxed">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {m.content}
                  </ReactMarkdown>
                </div>
                {/* Botón de descarga si el mensaje tiene PDF */}
                {m.pdfData && (
                  <button
                    onClick={() => downloadPdf(m.pdfData, m.pdfName || 'reporte_venom.pdf')}
                    className="mt-3 flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold py-1.5 px-3 rounded-full transition-colors"
                  >
                    <DocumentArrowDownIcon className="w-4 h-4" />
                    Descargar PDF
                  </button>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {loading && (
          <div className="flex justify-start items-center gap-3 text-gray-500 font-mono text-[10px] animate-pulse">
            <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" />
            PROCESANDO_RESPUESTA_VENOM...
          </div>
        )}
        
        <div ref={scrollRef} className="h-2" />
      </div>

      {/* CONTENEDOR DE INPUT */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-[#050505] via-[#050505] to-transparent pb-8 pt-20 z-30 px-4">
        <div className="max-w-4xl mx-auto">
          <AnimatePresence>
            {filePreview && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }} 
                className="mb-4 relative w-24 h-24 group"
              >
                {typeof filePreview === 'string' ? (
                  <img src={filePreview} className="w-full h-full object-cover rounded-xl border-2 border-purple-500 shadow-[0_0_15px_rgba(168,85,247,0.4)]" alt="preview" />
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center bg-white/5 rounded-xl border border-white/10">
                    <DocumentIcon className="w-8 h-8 text-purple-400" />
                    <span className="text-[10px] text-gray-400 mt-1 truncate max-w-full px-1">{filePreview.name}</span>
                  </div>
                )}
                <button onClick={() => setFile(null)} className="absolute -top-2 -right-2 bg-red-600 text-white rounded-full p-1 shadow-lg hover:bg-red-500 transition-colors">
                  <XMarkIcon className="w-4 h-4"/>
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="bg-[#111111]/90 backdrop-blur-xl border border-white/10 rounded-2xl p-2 flex items-center gap-2 focus-within:border-purple-500/50 focus-within:shadow-[0_0_20px_rgba(168,85,247,0.15)] transition-all">
            <input type="file" className="hidden" ref={fileInputRef} onChange={(e) => setFile(e.target.files[0])} />
            
            <button 
              onClick={() => fileInputRef.current.click()} 
              className={`p-2.5 rounded-xl transition-all ${file ? 'text-purple-400 bg-purple-400/10' : 'text-gray-500 hover:text-purple-400 hover:bg-white/5'}`}
            >
              <PlusCircleIcon className="w-6 h-6" />
            </button>

            <textarea 
              rows="1"
              className="flex-1 bg-transparent border-none text-white text-sm focus:ring-0 focus:outline-none resize-none py-3 px-1 outline-none"
              placeholder={loading ? "Venom está pensando..." : "Escribe tu comando... (puedes pegar imágenes)"}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
            />

            <button 
              onClick={sendMessage} 
              disabled={loading || (!input.trim() && !file)}
              className="bg-white text-black p-2.5 rounded-xl font-bold hover:bg-purple-600 hover:text-white transition-all disabled:opacity-10 disabled:cursor-not-allowed shadow-xl active:scale-95"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
              ) : (
                <PaperAirplaneIcon className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatLab;