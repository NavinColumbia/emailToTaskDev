import { useState, useCallback } from 'react';
import { api } from '../apis/api';
import { getToken } from '../apis/base';

export function useAuth() {
  const [authenticated, setAuthenticated] = useState<boolean>(!!getToken());
  const [loading, setLoading] = useState(true);

  const checkAuth = useCallback(async () => {
    setLoading(true);
    try {
      const isAuth = await api.checkAuth();
      setAuthenticated(isAuth);
      return isAuth;
    } catch (error) {
      console.error('Auth check failed:', error);
      setAuthenticated(false);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const authorize = useCallback(async () => {
    await api.authorize();
  }, []);

  const logout = useCallback(async () => {
    await api.logout();
    setAuthenticated(false);
  }, []);

  return {
    authenticated,
    loading,
    checkAuth,
    authorize,
    logout,
  };
}

