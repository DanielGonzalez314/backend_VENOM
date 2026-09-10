import { useState } from 'react';
import api from '../api/client';

export const useVenomChat = (conversationId) => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (query, file = null) => {
    setLoading(true);
    // Lógica de optimismo: añadir mensaje del usuario antes de la respuesta
    const userMsg = { role: 'user', content: query, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);

    const formData = new FormData();
    formData.append('query', query);
    if (file) formData.append('file', file);

    try {
      const endpoint = conversationId !== "default_conv" ? `/ask/${conversationId}` : '/ask-smart';
      const { data } = await api.post(endpoint, formData);
      
      const aiMsg = { role: 'assistant', content: data.answer || data.content };
      setMessages(prev => [...prev, aiMsg]);
      return data;
    } catch (err) {
      console.error("Error en el núcleo:", err);
    } finally {
      setLoading(false);
    }
  };

  return { messages, setMessages, sendMessage, loading };
};