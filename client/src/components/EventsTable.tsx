import { Box, Typography, Button, CircularProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';
import { Event as EventIcon, Refresh as RefreshIcon, OpenInNew as OpenInNewIcon } from '@mui/icons-material';
import { notionColors } from '../theme';
import { formatDate } from '../utils/dateUtils';
import type { CalendarEvent } from '../api';

interface EventsTableProps {
  events: CalendarEvent[];
  loading: boolean;
  onRefresh: () => void;
}

export default function EventsTable({ events, loading, onRefresh }: EventsTableProps) {
  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" sx={{ fontSize: '16px' }}>
          All Calendar Events ({events.length})
        </Typography>
        <Button
          variant="text"
          startIcon={<RefreshIcon sx={{ fontSize: 18 }} />}
          onClick={onRefresh}
          disabled={loading}
          sx={{ px: 1.5, py: 0.75 }}
        >
          Refresh
        </Button>
      </Box>

      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
          <CircularProgress size={24} />
        </Box>
      ) : events.length > 0 ? (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Event</TableCell>
                <TableCell>Location</TableCell>
                <TableCell>Start Time</TableCell>
                <TableCell>End Time</TableCell>
                <TableCell>From Email</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Action</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {events.map((event, idx) => (
                <TableRow key={idx}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <EventIcon sx={{ fontSize: 18, color: notionColors.text.secondary }} />
                      <Typography
                        variant="body2"
                        sx={{
                          maxWidth: 250,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          fontSize: '14px',
                        }}
                        title={event.summary}
                      >
                        {event.summary}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography
                      variant="body2"
                      sx={{
                        maxWidth: 150,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        fontSize: '14px',
                        color: notionColors.text.secondary,
                      }}
                      title={event.location || '—'}
                    >
                      {event.location || '—'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontSize: '14px' }}>
                      {event.start_datetime ? formatDate(event.start_datetime) : '—'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontSize: '14px' }}>
                      {event.end_datetime ? formatDate(event.end_datetime) : '—'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography
                      variant="body2"
                      sx={{
                        maxWidth: 200,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        fontSize: '14px',
                      }}
                      title={event.email_sender || 'Unknown'}
                    >
                      {event.email_sender || 'Unknown'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontSize: '14px' }}>
                      {formatDate(event.created_at)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Button
                      component="a"
                      href={event.html_link || "https://calendar.google.com/"}
                      target="_blank"
                      rel="noopener"
                      size="small"
                      startIcon={<OpenInNewIcon sx={{ fontSize: 14 }} />}
                      variant="outlined"
                      sx={{ fontSize: '12px', px: 1.5, py: 0.5 }}
                    >
                      Open
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Box sx={{ border: `1px solid ${notionColors.border.default}`, borderRadius: '3px', p: 6, textAlign: 'center' }}>
          <EventIcon sx={{ fontSize: 48, color: notionColors.text.disabled, mb: 2 }} />
          <Typography variant="h6" sx={{ mb: 1, fontSize: '16px', fontWeight: 500 }}>
            No Calendar Events Found
          </Typography>
          <Typography variant="body2" sx={{ fontSize: '14px' }}>
            No calendar events have been created yet. Process emails with meeting information to create calendar events.
          </Typography>
        </Box>
      )}
    </>
  );
}

