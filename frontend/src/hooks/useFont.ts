import { useState } from 'react';

import { electronAPI } from '../api/electronAPI';
import type {
  ConvertRequest,
  ConvertResponse,
  GenerateFontRequest,
  GenerateFontResponse,
  PreviewRequest,
  SubsetRequest,
  SubsetResponse,
} from '../../../shared/types/font';

/** Hook for font IPC actions with loading and error state. */
export function useFont() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async <T,>(task: () => Promise<T>): Promise<T> => {
    setLoading(true);
    setError(null);
    try {
      return await task();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    error,
    generate: (request: GenerateFontRequest): Promise<GenerateFontResponse> => run(() => electronAPI.font.generate(request)),
    subset: (request: SubsetRequest): Promise<SubsetResponse> => run(() => electronAPI.font.subset(request)),
    convert: (request: ConvertRequest): Promise<ConvertResponse> => run(() => electronAPI.font.convert(request)),
    preview: (request: PreviewRequest): Promise<Blob> => run(() => electronAPI.font.preview(request)),
  };
}

export default useFont;
