import { useState, useRef, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import { api } from '../api';

export function useKnowledgeUpload() {
  const { dispatch } = useApp();
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);

    try {
      await api.uploadRagDocument(file);
      const data = await api.getRagDocuments();
      dispatch({ type: 'SET_RAG_DOCUMENTS', payload: data });
    } catch (err) {
      setUploadError((err as Error).message || 'Upload failed');
    }

    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, [dispatch]);

  return {
    uploading,
    uploadError,
    setUploadError,
    fileInputRef,
    handleFileUpload,
  };
}
