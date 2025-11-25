import { useState, useEffect, useCallback } from 'react';
import { api, type Settings } from '../apis/api';

const DEFAULT_SETTINGS: Settings = {
  max: 10,
  window: '1d',
};

export function useSettings(authenticated: boolean) {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSettings = useCallback(async () => {
    if (!authenticated) {
      setSettings(DEFAULT_SETTINGS);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const savedSettings = await api.getSettings();
      setSettings(savedSettings);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load settings';
      setError(errorMessage);
      console.error('Failed to load settings:', err);
    } finally {
      setLoading(false);
    }
  }, [authenticated]);

  const saveSettings = useCallback(async (newSettings: Settings) => {
    if (!authenticated) {
      throw new Error('Not authenticated');
    }

    setSaving(true);
    setError(null);
    try {
      const savedSettings = await api.updateSettings(newSettings);
      setSettings(savedSettings);
      return savedSettings;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save settings';
      setError(errorMessage);
      throw err;
    } finally {
      setSaving(false);
    }
  }, [authenticated]);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  return {
    settings,
    loading,
    saving,
    error,
    setSettings,
    loadSettings,
    saveSettings,
  };
}

