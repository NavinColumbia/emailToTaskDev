import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  Snackbar,
  Alert,
  CircularProgress,
  TextField,
  Chip,
  FormControlLabel,
  Switch,
} from '@mui/material';
import {
  Save as SaveIcon,
  Add as AddIcon,
  Close as CloseIcon,
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
  const [newTaskCategory, setNewTaskCategory] = useState('');
  const [newCalendarCategory, setNewCalendarCategory] = useState('');

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

  const handleAddTaskCategory = () => {
    const trimmed = newTaskCategory.trim();
    if (trimmed && !settings.task_categories?.includes(trimmed)) {
      setSettings({
        ...settings,
        task_categories: [...(settings.task_categories || []), trimmed],
      });
      setNewTaskCategory('');
    }
  };

  const handleRemoveTaskCategory = (category: string) => {
    setSettings({
      ...settings,
      task_categories: settings.task_categories?.filter(c => c !== category) || [],
    });
  };

  const handleAddCalendarCategory = () => {
    const trimmed = newCalendarCategory.trim();
    if (trimmed && !settings.calendar_categories?.includes(trimmed)) {
      setSettings({
        ...settings,
        calendar_categories: [...(settings.calendar_categories || []), trimmed],
      });
      setNewCalendarCategory('');
    }
  };

  const handleRemoveCalendarCategory = (category: string) => {
    setSettings({
      ...settings,
      calendar_categories: settings.calendar_categories?.filter(c => c !== category) || [],
    });
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
      <Box sx={{ maxWidth: 1400, mx: 'auto', px: { xs: 2, sm: 3, md: 4 }, pt: 0 }}>
        <PageHeader 
          title="Settings"
          description="Configure default preferences for processing emails."
        />

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 6 }}>
            <Box sx={{ display: 'flex', flexDirection: 'row', gap: 2 }}>
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
            </Box>

            <FormControlLabel
              control={
                <Switch
                  checked={settings.auto_generate ?? true}
                  onChange={(e) => setSettings({ ...settings, auto_generate: e.target.checked })}
                  disabled={saving}
                />
              }
              label="Auto-generate tasks and calendar events"
              sx={{
                '& .MuiFormControlLabel-label': {
                  fontSize: '14px',
                  fontWeight: 400,
                },
              }}
            />

            <Box>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
                <TextField
                  label="Task Categories"
                  value={newTaskCategory}
                  onChange={(e) => setNewTaskCategory(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleAddTaskCategory();
                    }
                  }}
                  placeholder="Enter category name"
                  helperText="Only emails corresponding to these categories will be considered. If none selected, all emails are considered."
                  fullWidth
                  disabled={saving}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      backgroundColor: '#FFFFFF',
                      padding: '0px 14px',
                      display: 'flex',
                      alignItems: 'center',
                      '& .MuiInputBase-input': {
                        height: '53px',
                        padding: '0px',
                        boxSizing: 'border-box',
                        display: 'flex',
                        alignItems: 'center',
                      },
                    },
                  }}
                />
                <Button
                  onClick={handleAddTaskCategory}
                  variant="outlined"
                  startIcon={<AddIcon />}
                  disabled={saving || !newTaskCategory.trim()}
                  sx={{ 
                    height: '53px',
                  }}
                >
                  Add
                </Button>
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: settings.task_categories && settings.task_categories.length > 0 ? 2 : 0 }}>
                {settings.task_categories && settings.task_categories.length > 0 ? (
                  settings.task_categories.map((category) => (
                    <Chip
                      key={category}
                      label={category}
                      onDelete={() => handleRemoveTaskCategory(category)}
                      deleteIcon={<CloseIcon />}
                      disabled={saving}
                      sx={{
                        backgroundColor: notionColors.chip.default,
                        color: notionColors.chip.text,
                        '& .MuiChip-deleteIcon': {
                          fontSize: '14px',
                        },
                      }}
                    />
                  ))
                ) : null}
              </Box>
            </Box>

            <Box>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
                <TextField
                  label="Calendar Categories"
                  value={newCalendarCategory}
                  onChange={(e) => setNewCalendarCategory(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleAddCalendarCategory();
                    }
                  }}
                  placeholder="Enter category name"
                  helperText="Only emails corresponding to these categories will be considered. If none selected, all emails are considered."
                  fullWidth
                  disabled={saving}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      backgroundColor: '#FFFFFF',
                      padding: '0px 14px',
                      display: 'flex',
                      alignItems: 'center',
                      '& .MuiInputBase-input': {
                        height: '53px',
                        padding: '0px',
                        boxSizing: 'border-box',
                        display: 'flex',
                        alignItems: 'center',
                      },
                    },
                  }}
                />
                <Button
                  onClick={handleAddCalendarCategory}
                  variant="outlined"
                  startIcon={<AddIcon />}
                  disabled={saving || !newCalendarCategory.trim()}
                  sx={{ 
                    height: '53px',
                  }}
                >
                  Add
                </Button>
              </Box>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: settings.calendar_categories && settings.calendar_categories.length > 0 ? 2 : 0 }}>
                {settings.calendar_categories && settings.calendar_categories.length > 0 ? (
                  settings.calendar_categories.map((category) => (
                    <Chip
                      key={category}
                      label={category}
                      onDelete={() => handleRemoveCalendarCategory(category)}
                      deleteIcon={<CloseIcon />}
                      disabled={saving}
                      sx={{
                        backgroundColor: notionColors.chip.default,
                        color: notionColors.chip.text,
                        '& .MuiChip-deleteIcon': {
                          fontSize: '14px',
                        },
                      }}
                    />
                  ))
                ) : null}
              </Box>
            </Box>

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

