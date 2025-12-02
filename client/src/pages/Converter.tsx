/* eslint-disable react-hooks/set-state-in-effect */
import { useState, useEffect, useMemo } from 'react';
import {
  Box,
  Snackbar,
  Alert,
  Tabs,
  Tab,
  Typography,
  Chip,
} from '@mui/material';
import {
  Download as DownloadIcon,
  List as ListIcon,
  Event as EventIcon,
} from '@mui/icons-material';
import type { FetchEmailsParams, Task, CalendarEvent } from '../apis/api';
import { notionColors } from '../theme';
import { useTasks, useCalendarEvents, useFetchEmails, useSettings } from '../hooks';
import PageHeader from '../components/PageHeader';
import ProcessEmails from '../components/tabs/ProcessEmails';
import DataTable, { type Column } from '../components/tabs/DataTable';
import { formatDateOnly, formatTimeOnly } from '../utils/dateUtils';

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
      <Box sx={{ pt: 3, display: value === index ? 'block' : 'none' }}>{children}</Box>
    </div>
  );
}

export default function Converter({ authenticated }: ConverterProps) {
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'info' | 'warning'>('success');
  const [tabValue, setTabValue] = useState(0);
  
  const { tasks: allTasks, loading: loadingTasks, loadTasks, deleteTasks, confirmTasks } = useTasks();
  const { events: allCalendarEvents, loading: loadingCalendarEvents, loadEvents, deleteEvents, confirmEvents } = useCalendarEvents();
  const { loading, fetchEmails } = useFetchEmails();
  const { settings } = useSettings(authenticated);

  const handleOpenTasks = (tasks: Task[]) => {
    tasks.forEach(task => {
      if (task.task_link && task.status === 'created') {
        window.open(task.task_link, '_blank', 'noopener,noreferrer');
      }
    });
  };

  const handleOpenEvents = (events: CalendarEvent[]) => {
    events.forEach(event => {
      if (event.html_link && event.status === 'created') {
        window.open(event.html_link, '_blank', 'noopener,noreferrer');
      }
    });
  };

  const handleConfirmTasks = async (taskIds: number[]) => {
    try {
      await confirmTasks(taskIds);
      setSnackbarMessage(`Successfully confirmed ${taskIds.length} task(s)`);
      setSnackbarSeverity('success');
      setShowSnackbar(true);
      loadTasks().catch(() => {});
    } catch (err) {
      setSnackbarMessage(err instanceof Error ? err.message : 'Failed to confirm tasks');
      setSnackbarSeverity('error');
      setShowSnackbar(true);
    }
  };

  const handleConfirmEvents = async (eventIds: number[]) => {
    try {
      await confirmEvents(eventIds);
      setSnackbarMessage(`Successfully confirmed ${eventIds.length} event(s)`);
      setSnackbarSeverity('success');
      setShowSnackbar(true);
      loadEvents().catch(() => {});
    } catch (err) {
      setSnackbarMessage(err instanceof Error ? err.message : 'Failed to confirm events');
      setSnackbarSeverity('error');
      setShowSnackbar(true);
    }
  };

  const handleDeleteTasks = async (taskIds: number[]) => {
    try {
      await deleteTasks(taskIds);
      setSnackbarMessage(`Successfully deleted ${taskIds.length} task(s)`);
      setSnackbarSeverity('success');
      setShowSnackbar(true);
      loadTasks().catch(() => {});
    } catch (err) {
      setSnackbarMessage(err instanceof Error ? err.message : 'Failed to delete tasks');
      setSnackbarSeverity('error');
      setShowSnackbar(true);
    }
  };

  const handleDeleteEvents = async (eventIds: number[]) => {
    try {
      await deleteEvents(eventIds);
      setSnackbarMessage(`Successfully deleted ${eventIds.length} event(s)`);
      setSnackbarSeverity('success');
      setShowSnackbar(true);
      loadEvents().catch(() => {});
    } catch (err) {
      setSnackbarMessage(err instanceof Error ? err.message : 'Failed to delete events');
      setSnackbarSeverity('error');
      setShowSnackbar(true);
    }
  };

  // Task table columns
  const taskColumns: Column<Task>[] = useMemo(() => {
    const hasCategories = settings?.task_categories && settings.task_categories.length > 0;
    
    const columns: Column<Task>[] = [
      {
        header: 'Title',
        render: (task) => (
          <Typography variant="body2" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '14px' }}>
            {task.task_title || task.email_subject || '(no title)'}
          </Typography>
        ),
      },
      {
        header: 'Status',
        render: (task) => {
          const statusLabels: Record<string, string> = {
            'pending': 'Pending',
            'created': 'Created',
            'skipped': 'Skipped',
          };
          const statusColors: Record<string, { bg: string; text: string }> = {
            'pending': { bg: notionColors.warning?.background || '#FFF4E5', text: notionColors.warning?.text || '#B7791F' },
            'created': { bg: notionColors.chip.success, text: notionColors.chip.successText },
            'skipped': { bg: notionColors.error.background, text: notionColors.error.text },
          };
          const colors = statusColors[task.status] || statusColors['skipped'];
          return (
            <Chip 
              label={statusLabels[task.status] || 'Unknown'} 
              size="small"
              sx={{ 
                backgroundColor: colors.bg,
                color: colors.text,
                maxWidth: '100%',
                fontWeight: 500,
                '& .MuiChip-label': {
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }
              }} 
            />
          );
        },
      },
    ];

    // Only add Category column if there are categories in settings
    if (hasCategories) {
      columns.push({
        header: 'Category',
        render: (task) => (
          <Chip 
            label={task.category || 'Uncategorized'} 
            size="small"
            variant="outlined"
            sx={{ 
              borderColor: notionColors.border.default,
              color: task.category ? notionColors.text.primary : notionColors.text.disabled,
              maxWidth: '100%',
              '& .MuiChip-label': {
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }
            }} 
          />
        ),
      });
    }

    columns.push(
      {
        header: 'Sender',
        render: (task) => (
          <Typography variant="body2" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '14px', color: notionColors.text.secondary }}>
            {task.email_sender || 'Unknown'}
          </Typography>
        ),
      },
      {
        header: 'Provider',
        render: (task) => (
          <Chip 
            label={task.provider} 
            size="small"
            sx={{ 
              backgroundColor: notionColors.chip.default,
              color: notionColors.primary.main,
              maxWidth: '100%',
              fontWeight: 500,
              '& .MuiChip-label': {
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }
            }} 
          />
        ),
      },
      {
        header: 'Due Date',
        render: (task) => (
          <Typography variant="body2" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '14px', color: notionColors.text.secondary }}>
            {task.task_due || '—'}
          </Typography>
        ),
      }
    );

    return columns;
  }, [settings]);

  // Event table columns
  const eventColumns: Column<CalendarEvent>[] = useMemo(() => {
    const hasCategories = settings?.calendar_categories && settings.calendar_categories.length > 0;
    
    const columns: Column<CalendarEvent>[] = [
      {
        header: 'Event',
        render: (event) => (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, overflow: 'hidden' }}>
            <Typography variant="body2" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '14px' }}>
              {event.summary || 'Meeting'}
            </Typography>
          </Box>
        ),
      },
      {
        header: 'Status',
        render: (event) => {
          const statusLabels: Record<string, string> = {
            'pending': 'Pending',
            'created': 'Created',
            'skipped': 'Skipped',
          };
          const statusColors: Record<string, { bg: string; text: string }> = {
            'pending': { bg: notionColors.warning?.background || '#FFF4E5', text: notionColors.warning?.text || '#B7791F' },
            'created': { bg: notionColors.chip.success, text: notionColors.chip.successText },
            'skipped': { bg: notionColors.error.background, text: notionColors.error.text },
          };
          const colors = statusColors[event.status] || statusColors['skipped'];
          return (
            <Chip 
              label={statusLabels[event.status] || 'Unknown'} 
              size="small"
              sx={{ 
                backgroundColor: colors.bg,
                color: colors.text,
                maxWidth: '100%',
                fontWeight: 500,
                '& .MuiChip-label': {
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }
              }} 
            />
          );
        },
      },
    ];

    // Only add Category column if there are categories in settings
    if (hasCategories) {
      columns.push({
        header: 'Category',
        render: (event) => (
          <Chip 
            label={event.category || 'Uncategorized'} 
            size="small"
            variant="outlined"
            sx={{ 
              borderColor: notionColors.border.default,
              color: event.category ? notionColors.text.primary : notionColors.text.disabled,
              maxWidth: '100%',
              '& .MuiChip-label': {
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }
            }} 
          />
        ),
      });
    }

    columns.push(
      {
        header: 'Location',
        render: (event) => (
          <Typography variant="body2" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '14px', color: notionColors.text.secondary }}>
            {event.location || '—'}
          </Typography>
        ),
      },
      {
        header: 'Date',
        render: (event) => (
          <Typography variant="body2" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '14px' }}>
            {event.start_datetime ? formatDateOnly(event.start_datetime) : '—'}
          </Typography>
        ),
      },
      {
        header: 'Start Time',
        render: (event) => (
          <Typography variant="body2" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '14px' }}>
            {event.start_datetime ? formatTimeOnly(event.start_datetime) : '—'}
          </Typography>
        ),
      },
      {
        header: 'End Time',
        render: (event) => (
          <Typography variant="body2" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '14px' }}>
            {event.end_datetime ? formatTimeOnly(event.end_datetime) : '—'}
          </Typography>
        ),
      },
      {
        header: 'From Email',
        render: (event) => (
          <Typography variant="body2" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '14px', color: notionColors.text.secondary }}>
            {event.email_sender || 'Unknown'}
          </Typography>
        ),
      }
    );

    return columns;
  }, [settings]);
  
  // Compute base formData from settings
  const baseFormData = useMemo<FetchEmailsParams>(() => ({
    provider: 'google_tasks',
    max: settings?.max,
    window: settings?.window || '',
    since: '',
    q: '',
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
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const params: FetchEmailsParams = {
        ...formData,
        provider: 'google_tasks', // Always use Google Tasks
        max: formData.max ? Number(formData.max) : undefined,
        timezone,
      };

      const result = await fetchEmails(params);
      const calendarCount = result.calendar_events?.length || 0;

      if (result.processed === 0 && result.already_processed === 0 && calendarCount === 0) {
        setSnackbarMessage('No emails found matching your criteria.');
        setSnackbarSeverity('warning');
        setShowSnackbar(true);
      } else if (result.processed === 0 && result.already_processed > 0 && calendarCount === 0) {
        setSnackbarMessage(`Found ${result.already_processed} emails, but they were already processed. No new tasks created.`);
        setSnackbarSeverity('info');
        setShowSnackbar(true);
      } else {
        let message = '';
        if (result.processed > 0) {
          message = `Successfully processed ${result.processed} email${result.processed > 1 ? 's' : ''} and created ${result.processed} task${result.processed > 1 ? 's' : ''}`;
        } else if (calendarCount > 0) {
          message = `Processed emails and created ${calendarCount} calendar event(s).`;
        } else {
          message = `Found ${result.already_processed} emails, but they were already processed.`;
        }
        
        if (result.processed > 0 && calendarCount > 0) {
          message += ` Also created ${calendarCount} calendar event(s).`;
        }
        
        setSnackbarMessage(message);
        setSnackbarSeverity('success');
        setShowSnackbar(true);
        loadTasks().catch(() => {});
        loadEvents().catch(() => {});
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
      <Box sx={{ maxWidth: 1400, mx: 'auto', px: { xs: 2, sm: 3, md: 4 }, pt: 0 }}>
        <Box sx={{ mb: 4 }}>
          <PageHeader />

          <Box sx={{ borderBottom: `2px solid ${notionColors.border.light}`, mb: 4 }}>
            <Tabs 
              value={tabValue} 
              onChange={(_, newValue) => setTabValue(newValue)}
              sx={{
                '& .MuiTab-root': {
                  minHeight: 48,
                  '&.Mui-selected': {
                    color: notionColors.primary.main,
                  },
                },
              }}
            >
              <Tab 
                label="Process Emails" 
                icon={<DownloadIcon sx={{ fontSize: 18, color: tabValue === 0 ? notionColors.primary.main : 'inherit' }} />} 
                iconPosition="start" 
              />
              <Tab 
                label="All Tasks" 
                icon={<ListIcon sx={{ fontSize: 18, color: tabValue === 1 ? notionColors.primary.main : 'inherit' }} />} 
                iconPosition="start" 
              />
              <Tab 
                label="Calendar" 
                icon={<EventIcon sx={{ fontSize: 18, color: tabValue === 2 ? notionColors.primary.main : 'inherit' }} />} 
                iconPosition="start" 
              />
            </Tabs>
            </Box>

          <TabPanel value={tabValue} index={0}>
            <ProcessEmails
              formData={formData}
              onFormDataChange={setFormData}
              onSubmit={handleSubmit}
              loading={loading}
            />
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <DataTable
              data={allTasks}
              loading={loadingTasks}
              columns={taskColumns}
              emptyIcon={<ListIcon sx={{ fontSize: 48, color: notionColors.text.disabled, mb: 2 }} />}
              emptyTitle="No Tasks Found"
              emptyMessage="No tasks have been processed yet. Start by processing emails from your Gmail account."
              getItemId={(task) => task.id}
              onOpen={handleOpenTasks}
              onDelete={handleDeleteTasks}
              onConfirm={handleConfirmTasks}
              getItemLink={(task) => task.status === 'created' ? task.task_link : undefined}
              getItemStatus={(task) => task.status}
            />
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <DataTable
              data={allCalendarEvents}
              loading={loadingCalendarEvents}
              columns={eventColumns}
              emptyIcon={<EventIcon sx={{ fontSize: 48, color: notionColors.text.disabled, mb: 2 }} />}
              emptyTitle="No Calendar Events Found"
              emptyMessage="No calendar events have been created yet. Process emails with meeting information to create calendar events."
              getItemId={(event) => event.id}
              onOpen={handleOpenEvents}
              onDelete={handleDeleteEvents}
              onConfirm={handleConfirmEvents}
              getItemLink={(event) => event.status === 'created' ? event.html_link : undefined}
              getItemStatus={(event) => event.status}
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

