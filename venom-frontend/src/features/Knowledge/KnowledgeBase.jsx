import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../../api/client';
import { 
  CloudArrowUpIcon, 
  DocumentIcon, 
  TableCellsIcon, 
  CheckCircleIcon,
  TrashIcon,
  CircleStackIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

const KnowledgeBase = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  // 1. CARGA DE DATOS (Sincronizada con el Data Lake)
  const fetchDocuments = useCallback(async () => {
    try {
      const response = await api.get('/documents');
      const formattedFiles = response.data.map(doc => ({
        id: doc.id,
        name: doc.filename,
        size: doc.file_size ? (doc.file_size / 1024).toFixed(2) + ' KB' : '0 KB',
        type: doc.filename.split('.').pop().toLowerCase(),
        date: doc.created_at 
      }));
      setFiles(formattedFiles);
    } catch (error) {
      console.error("Error cargando el Data Lake:", error);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // 2. LÓGICA DE INGESTA (Upload)
  const handleUpload = async (e) => {
    e.preventDefault();
    e.stopPropagation();

    const selectedFiles = e.target.files || e.dataTransfer?.files;
    if (!selectedFiles || !selectedFiles[0]) return;

    const fileToUpload = selectedFiles[0];
    setUploading(true);

    const formData = new FormData();
    formData.append('file', fileToUpload);

    try {
      await api.post('/ingest/file', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      await fetchDocuments();
    } catch (error) {
      console.error("Error en la ingesta:", error);
      alert(error.response?.data?.detail || "Error en los protocolos de ingesta");
    } finally {
      setUploading(false);
      setDragActive(false);
    }
  };

  // 3. LÓGICA DE PURGA (Delete)
  const deleteDocument = async (id) => {
    if (!window.confirm("¿Confirmas la purga total de este documento del motor vectorial?")) return;

    try {
      await api.delete(`/documents/${id}`);
      setFiles(prev => prev.filter(f => f.id !== id));
    } catch (error) {
      console.error("Fallo en la purga:", error);
      alert("Error al intentar purgar el archivo del Data Lake");
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-10 p-6 pb-20">
      
      {/* HEADER DINÁMICO */}
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="flex flex-col md:flex-row md:items-end justify-between gap-6"
      >
        <div>
          <div className="flex items-center gap-3 mb-2">
            <CircleStackIcon className="w-8 h-8 text-purple-500" />
            <h2 className="text-4xl font-black tracking-tighter text-white uppercase italic">Neural_Data_Lake</h2>
          </div>
          <p className="text-gray-500 font-mono text-xs uppercase tracking-widest">
            Repositorio de Inteligencia // {files.length} Documentos Indexados
          </p>
        </div>

        <div className="flex items-center gap-4 bg-white/[0.03] border border-white/5 p-3 rounded-2xl">
            <div className="text-right">
                <p className="text-[10px] text-gray-500 font-bold uppercase tracking-tighter">Status del Motor</p>
                <p className="text-xs text-green-400 font-mono">VECTOR_SYNC_ACTIVE</p>
            </div>
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_10px_#22c55e]" />
        </div>
      </motion.div>

      {/* ZONA DE CARGA ESTILO INDUSTRIAL */}
      <motion.div
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleUpload}
        className={`relative border-2 border-dashed rounded-[2.5rem] p-16 transition-all flex flex-col items-center justify-center overflow-hidden group
          ${dragActive ? 'border-purple-500 bg-purple-500/10 scale-[1.01]' : 'border-white/10 bg-[#0a0a0a] hover:bg-white/[0.02]'}`}
      >
        <input 
          type="file" 
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
          onChange={handleUpload}
          disabled={uploading}
          accept=".pdf,.xlsx,.xls,.csv,.txt"
        />
        
        <div className="relative mb-6">
          {uploading ? (
            <div className="relative">
                <div className="w-16 h-16 border-2 border-purple-500/20 rounded-full" />
                <motion.div 
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
                    className="absolute inset-0 w-16 h-16 border-t-2 border-purple-500 rounded-full"
                />
            </div>
          ) : (
            <div className="p-5 bg-white/5 rounded-3xl group-hover:bg-purple-500/20 transition-all group-hover:scale-110">
                <CloudArrowUpIcon className="w-10 h-10 text-purple-400" />
            </div>
          )}
        </div>
        
        <p className="text-xl font-bold text-white text-center tracking-tight">
          {uploading ? "Sincronizando con Venom Core..." : "Protocolo de Ingesta de Datos"}
        </p>
        <p className="text-sm text-gray-500 mt-2 font-mono uppercase tracking-tighter">PDF, EXCEL, CSV, TXT (MAX 25MB)</p>
      </motion.div>

      {/* GRID DE DOCUMENTOS */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <AnimatePresence mode='popLayout'>
          {files.map((file) => (
            <motion.div
              key={file.id}
              layout
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="flex items-center p-5 bg-[#0d0d0d] border border-white/5 rounded-3xl gap-4 hover:border-purple-500/40 transition-all group relative overflow-hidden"
            >
              {/* Indicador de Vectorizado */}
              <div className="absolute top-0 right-0 p-2 opacity-20 group-hover:opacity-100 transition-opacity">
                <CheckCircleIcon className="w-4 h-4 text-purple-500" />
              </div>

              <div className="p-3 bg-white/5 rounded-2xl group-hover:bg-purple-500/10 transition-colors shadow-inner">
                {['xlsx', 'xls', 'csv'].includes(file.type) ? (
                  <TableCellsIcon className="w-7 h-7 text-green-400" />
                ) : (
                  <DocumentIcon className="w-7 h-7 text-blue-400" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-black truncate text-gray-100 uppercase tracking-tight">{file.name}</p>
                <div className="flex items-center gap-2 mt-1">
                    <span className="text-[9px] font-mono text-purple-500/80 bg-purple-500/5 px-2 py-0.5 rounded border border-purple-500/10">
                        {file.size}
                    </span>
                    <span className="text-[9px] text-gray-600 font-bold uppercase tracking-widest">
                        Ready_to_Read
                    </span>
                </div>
              </div>

              {/* Botón de Purga */}
              <button 
                onClick={() => deleteDocument(file.id)}
                className="p-2 hover:bg-red-500/10 rounded-xl text-gray-600 hover:text-red-500 transition-all transform hover:rotate-12"
              >
                <TrashIcon className="w-5 h-5" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* EMPTY STATE */}
      {files.length === 0 && !uploading && (
        <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-24 border border-white/5 rounded-[3rem] bg-white/[0.01] flex flex-col items-center"
        >
          <ExclamationTriangleIcon className="w-12 h-12 text-gray-800 mb-4" />
          <p className="text-gray-600 font-mono text-sm uppercase tracking-[0.3em]">Neural_Lake_Is_Empty</p>
          <p className="text-[10px] text-gray-700 mt-2 uppercase">Sube un archivo para iniciar la vectorización</p>
        </motion.div>
      )}
    </div>
  );
};

export default KnowledgeBase;