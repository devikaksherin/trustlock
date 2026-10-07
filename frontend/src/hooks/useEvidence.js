import { useState, useCallback } from 'react';
import { uploadEvidence, deleteEvidence } from '../services/api';

export function useEvidence() {
  const [evidenceList, setEvidenceList] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const addFiles = useCallback(async (files) => {
    setUploadError(null);
    setIsUploading(true);
    setUploadProgress(0);
    
    const newEvidences = [];
    const totalFiles = files.length;
    
    try {
      for (let i = 0; i < totalFiles; i++) {
        const file = files[i];
        const result = await uploadEvidence(file, {
          onProgress: (p) => {
            const overallProgress = (i + p) / totalFiles;
            setUploadProgress(overallProgress);
          }
        });
        newEvidences.push(result);
      }
      setEvidenceList(prev => [...prev, ...newEvidences]);
      setUploadProgress(1);
      return newEvidences;
    } catch (err) {
      setUploadError(err.message || "Failed to upload evidence.");
      return null;
    } finally {
      setIsUploading(false);
    }
  }, []);

  const removeEvidence = useCallback(async (id) => {
    try {
      await deleteEvidence(id);
    } catch (err) {
      console.warn("Failed to delete from server:", err);
    }
    setEvidenceList(prev => prev.filter(e => e.id !== id));
  }, []);
  
  const resetEvidence = useCallback(() => {
    setEvidenceList([]);
    setUploadError(null);
    setUploadProgress(0);
  }, []);
  
  const setInitialEvidence = useCallback((list) => {
    setEvidenceList(list);
  }, []);

  return {
    evidenceList,
    isUploading,
    uploadError,
    uploadProgress,
    addFiles,
    removeEvidence,
    resetEvidence,
    setInitialEvidence
  };
}
