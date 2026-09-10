import { useState, useEffect } from 'react';
import api from '../api';

export const useDataLake = () => {
  const [documents, setDocuments] = useState([]);
  const [isSyncing, setIsSyncing] = useState(false);

  const refreshDocs = async () => {
    setIsSyncing(true);
    try {
      const { data } = await api.get('/documents');
      setDocuments(data);
    } finally {
      setIsSyncing(false);
    }
  };

  useEffect(() => { refreshDocs(); }, []);

  return { documents, isSyncing, refreshDocs };
};