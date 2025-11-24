/* eslint-disable react-hooks/set-state-in-effect */
import { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Snackbar,
  Alert,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Download as DownloadIcon,
  List as ListIcon,
  Event as EventIcon,
} from '@mui/icons-material';
import type { FetchEmailsParams } from '../api';
import { notionColors } from '../theme';
import { useTasks, useCalendarEvents, useFetchEmails, useSettings } from '../hooks';
import PageHeader from '../components/PageHeader';
import ProcessEmailsForm from '../components/ProcessEmailsForm';
import CreatedTasksList from '../components/CreatedTasksList';
import CreatedCalendarEvents from '../components/CreatedCalendarEvents';
import AllTasksTable from '../components/AllTasksTable';
import AllCalendarEventsTable from '../components/AllCalendarEventsTable';

interface ConverterProps {
  authenticated: boolean;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

export default function Converter({ authenticated }: ConverterProps) {
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'info' | 'warning'>('success');
  const [tabValue, setTabValue] = useState(0);
  
  const { tasks: allTasks, loading: loadingTasks, loadTasks } = useTasks();
  const { events: allCalendarEvents, loading: loadingCalendarEvents, loadEvents } = useCalendarEvents();
  const { result: results, loading, error, fetchEmails } = useFetchEmails();
  const { settings } = useSettings(authenticated);
  
  // Compute base formData from settings
  const baseFormData = useMemo<FetchEmailsParams>(() => ({
    provider: 'google_tasks', // Always use Google Tasks
    max: settings?.max,
    window: settings?.window || '',
    since_hours: undefined,
    since: '',
    q: '',
    dry_run: settings?.dry_run || false,
  }), [settings]);
  
  const [formData, setFormData] = useState<FetchEmailsParams>(baseFormData);


  useEffect(() => {
    if (authenticated && settings) {
      setFormData(baseFormData);
    }
  }, [authenticated, settings, baseFormData]);

  useEffect(() => {
    if (authenticated && tabValue === 1) {
      loadTasks().catch((err) => {
        setSnackbarMessage(err instanceof Error ? err.message : 'Failed to load tasks');
        setSnackbarSeverity('error');
        setShowSnackbar(true);
      });
    } else if (authenticated && tabValue === 2) {
      loadEvents().catch((err) => {
        setSnackbarMessage(err instanceof Error ? err.message : 'Failed to load calendar events');
        setSnackbarSeverity('error');
        setShowSnackbar(true);
      });
    }
  }, [authenticated, tabValue, loadTasks, loadEvents]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const params: FetchEmailsParams = {
        ...formData,
        provider: 'google_tasks', // Always use Google Tasks
        max: formData.max ? Number(formData.max) : undefined,
        since_hours: formData.since_hours ? Number(formData.since_hours) : undefined,
        dry_run: formData.dry_run || false,
      };

      const result = await fetchEmails(params);

      if (result.processed === 0 && result.already_processed === 0) {
        setSnackbarMessage('No emails found matching your criteria.');
        setSnackbarSeverity('warning');
        setShowSnackbar(true);
      } else if (result.processed === 0 && result.already_processed > 0) {
        setSnackbarMessage(`Found ${result.already_processed} emails, but they were already processed. No new tasks created.`);
        setSnackbarSeverity('info');
        setShowSnackbar(true);
      } else {
        const calendarCount = result.calendar_events?.length || 0;
        let message = `Successfully processed ${result.processed} email(s) and created ${result.processed} task(s)!`;
        if (calendarCount > 0) {
          message += ` Also created ${calendarCount} calendar event(s).`;
        }
        setSnackbarMessage(message);
        setSnackbarSeverity('success');
        setShowSnackbar(true);
        if (tabValue === 1) {
          loadTasks().catch(() => {});
        } else if (tabValue === 2) {
          loadEvents().catch(() => {});
        }
      }
    } catch (err) {
      setSnackbarMessage(err instanceof Error ? err.message : 'An error occurred');
      setSnackbarSeverity('error');
      setShowSnackbar(true);
    }
  };

  if (!authenticated) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
        <Box sx={{ textAlign: 'center', maxWidth: 600, px: 3 }}>
          <Box sx={{ color: notionColors.text.secondary }}>
            Please authenticate to access the Email to Task Converter.
          </Box>
        </Box>
      </Box>
    );
  }

    return (
      <>
      <Box sx={{ maxWidth: 900, mx: 'auto', px: 3, pt: 4 }}>
        <Box sx={{ mb: 4 }}>
          <PageHeader />

          <Box sx={{ borderBottom: `1px solid ${notionColors.border.default}`, mb: 4 }}>
            <Tabs 
              value={tabValue} 
              onChange={(_, newValue) => setTabValue(newValue)}
            >
              <Tab label="Process Emails" icon={<DownloadIcon sx={{ fontSize: 18 }} />} iconPosition="start" />
              <Tab label="All Tasks" icon={<ListIcon sx={{ fontSize: 18 }} />} iconPosition="start" />
              <Tab label="Calendar" icon={<EventIcon sx={{ fontSize: 18 }} />} iconPosition="start" />
            </Tabs>
            </Box>

          <TabPanel value={tabValue} index={0}>
            <ProcessEmailsForm
              formData={formData}
              onFormDataChange={setFormData}
              onSubmit={handleSubmit}
              loading={loading}
              error={error}
            />
            {results && (
              <>
                <CreatedTasksList results={results} />
                <CreatedCalendarEvents results={results} />
              </>
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <AllTasksTable
              tasks={allTasks}
              loading={loadingTasks}
              onRefresh={loadTasks}
            />
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <AllCalendarEventsTable
              events={allCalendarEvents}
              loading={loadingCalendarEvents}
              onRefresh={loadEvents}
            />
          </TabPanel>
              </Box>
            </Box>

        <Snackbar
          open={showSnackbar}
        autoHideDuration={6000}
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

