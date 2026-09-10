import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import DashboardLayout from './layouts/DashboardLayout';
import ChatLab from './features/chat/ChatLab';
import KnowledgeBase from './features/knowledge/KnowledgeBase';
import Login from './features/auth/Login';
import CompanyRegistry from './features/auth/CompanyRegistry';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="h-screen bg-[#050505] flex flex-col items-center justify-center text-white font-mono uppercase tracking-[0.3em]">
        <div className="w-12 h-12 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mb-4"></div>
        Iniciando Red...
      </div>
    );
  }
  
  return user ? children : <Navigate to="/login" replace />;
};

function App() {
  const [currentConversationId, setCurrentConversationId] = useState('new');

  return (
    <AuthProvider>
      <BrowserRouter>
        <AnimatePresence mode="wait">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<CompanyRegistry />} />

            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <DashboardLayout 
                    currentConversationId={currentConversationId}
                    onSelectConversation={setCurrentConversationId}
                  />
                </ProtectedRoute>
              }
            >
              {/* CORRECCIÓN AQUÍ: Debe ser <Route index ... /> */}
              <Route 
                index 
                element={
                  <ChatLab 
                    conversationId={currentConversationId} 
                    setConversationId={setCurrentConversationId} 
                  />
                } 
              />
              <Route path="knowledge" element={<KnowledgeBase />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AnimatePresence>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;