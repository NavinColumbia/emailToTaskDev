import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  Snackbar,
  Alert,
  Paper,
  CircularProgress,
} from '@mui/material';
import {
  Save as SaveIcon,
} from '@mui/icons-material';
import { notionColors } from '../theme';
import { useSettings } from '../hooks';
import PageHeader from '../components/PageHeader';
import MaxEmails from '../components/filter-inputs/MaxEmails';
import TimeWindow from '../components/filter-inputs/TimeWindow';

interface SettingsProps {
  authenticated: boolean;
}

export default function Settings({ authenticated }: SettingsProps) {
  const { settings, loading, saving, error, setSettings, saveSettings } = useSettings(authenticated);
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');

  const handleSave = async () => {
    try {
      await saveSettings(settings);
      setSnackbarMessage('Settings saved successfully!');
      setSnackbarSeverity('success');
      setShowSnackbar(true);
    } catch (error) {
      setSnackbarMessage(error instanceof Error ? error.message : 'Failed to save settings');
      setSnackbarSeverity('error');
      setShowSnackbar(true);
    }
  };

  // Show error snackbar when error changes
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setSnackbarMessage(error);
        setSnackbarSeverity('error');
        setShowSnackbar(true);
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [error]);

  if (!authenticated) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
        <Typography variant="body1" sx={{ color: notionColors.text.secondary }}>
          Please authenticate to access settings.
        </Typography>
      </Box>
    );
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <>
      <Box sx={{ maxWidth: 1400, mx: 'auto', px: 3, pt: 4 }}>
        <PageHeader 
          title="Settings"
          description="Configure default preferences for processing emails."
        />

        <Paper 
          elevation={0}
          sx={{ 
            p: 3, 
            border: `1.5px solid ${notionColors.border.default}`,
            borderRadius: 3,
            backgroundColor: '#FFFFFF',
            boxShadow: notionColors.shadow.card,
          }}
        >
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <MaxEmails
              value={settings.max}
              onChange={(max) => setSettings({ ...settings, max })}
              label="Default Max Emails"
              placeholder="No limit"
              helperText="Maximum number of emails to process by default (leave empty for no limit)"
              fullWidth
              disabled={saving}
            />

            <TimeWindow
              value={settings.window}
              onChange={(window) => setSettings({ ...settings, window })}
              label="Default Time Window"
              helperText="Default time window for email search"
              fullWidth
              disabled={saving}
              showCustomOption={false}
            />

            <Box sx={{ display: 'flex', justifyContent: 'flex-start', mt: 2 }}>
              <Button
                onClick={handleSave}
                variant="contained"
                startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
                disabled={saving}
                sx={{
                  px: 3,
                  py: 1,
                }}
              >
                {saving ? 'Saving...' : 'Save Settings'}
              </Button>
            </Box>
          </Box>
        </Paper>
      </Box>

      <Snackbar
        open={showSnackbar}
        autoHideDuration={4000}
        onClose={() => setShowSnackbar(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setShowSnackbar(false)} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </>
  );
}

