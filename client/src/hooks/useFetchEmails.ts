import { useState, useCallback } from 'react';
import { api, type FetchEmailsParams, type FetchEmailsResponse } from '../apis/api';

export function useFetchEmails() {
  const [result, setResult] = useState<FetchEmailsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEmails = useCallback(async (params: FetchEmailsParams) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await api.fetchEmails(params);
      setResult(response);
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch emails';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return {
    result,
    loading,
    error,
    fetchEmails,
    reset,
  };
}

