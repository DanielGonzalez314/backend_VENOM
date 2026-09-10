import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';

const DashboardLayout = ({ currentConversationId, onSelectConversation }) => {
  return (
    <div className="flex h-screen w-full bg-[#050505] overflow-hidden text-gray-100 font-sans">
      
      {/* 
        SIDEBAR: 
        Fija a la izquierda, con sombra para dar profundidad sobre el contenido.
      */}
      <aside className="w-72 flex-shrink-0 border-r border-white/5 bg-[#080808] relative z-50 shadow-[10px_0_30px_rgba(0,0,0,0.5)]">
        <Sidebar 
          currentConversationId={currentConversationId} 
          onSelectConversation={onSelectConversation} 
        />
      </aside>

      {/* 
        CONTENEDOR PRINCIPAL:
        Aquí es donde vive el ChatLab o KnowledgeBase.
      */}
      <main className="flex-1 relative flex flex-col min-w-0 bg-[#050505]">
        
        {/* 
           CAPA DE DECORACIÓN (Luces de fondo): 
           El 'pointer-events-none' es CRÍTICO para que puedas hacer clic 
           en los mensajes del chat sin que estas luces interfieran.
        */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden z-0">
          <div className="absolute top-[-5%] right-[-5%] w-[50%] h-[50%] bg-purple-900/10 blur-[120px] rounded-full opacity-60" />
          <div className="absolute bottom-[-5%] left-[-5%] w-[40%] h-[40%] bg-indigo-900/5 blur-[100px] rounded-full opacity-40" />
          
          {/* Sutil ruido de fondo para textura premium */}
          <div className="absolute inset-0 opacity-[0.015] bg-[url('https://grainy-gradients.vercel.app/noise.svg')]" />
        </div>

        {/* 
          ÁREA DE RENDERIZADO DINÁMICO:
          - 'flex flex-col items-center': Asegura que el contenido esté centrado horizontalmente.
          - 'overflow-hidden': Evita que el layout general se rompa si el hijo crece.
        */}
        <div className="flex-1 w-full relative z-10 flex flex-col items-center overflow-hidden">
          {/* 
             El Outlet actúa como el contenedor de ChatLab/Knowledge. 
             Le pasamos el contexto por si los hijos lo necesitan.
          */}
          <div className="w-full h-full max-w-[1600px] flex flex-col">
            <Outlet context={{ currentConversationId, onSelectConversation }} />
          </div>
        </div>

      </main>
    </div>
  );
};

export default DashboardLayout;