import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Button } from '@mui/material';
import { Event as EventIcon, OpenInNew as OpenInNewIcon } from '@mui/icons-material';
import { notionColors } from '../theme';
import { formatDate } from '../utils/dateUtils';
import type { FetchEmailsResponse, CalendarEvent } from '../api';

interface EventsTableProps {
  results?: FetchEmailsResponse;
  allEvents?: CalendarEvent[];
  loading?: boolean;
}

export default function EventsTable({ results, allEvents, loading }: EventsTableProps) {
  // Handle all events view
  if (allEvents !== undefined) {
    if (loading) {
  return (
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <Typography variant="body1" sx={{ color: notionColors.text.secondary }}>
            Loading calendar events...
        </Typography>
      </Box>
      );
    }

    if (allEvents.length === 0) {
      return (
        <Box sx={{ border: `1px solid ${notionColors.border.default}`, borderRadius: '3px', p: 6, textAlign: 'center' }}>
          <EventIcon sx={{ fontSize: 48, color: notionColors.text.disabled, mb: 2 }} />
          <Typography variant="h6" sx={{ mb: 1, fontSize: '16px', fontWeight: 500 }}>
            No Calendar Events Found
          </Typography>
          <Typography variant="body2" sx={{ fontSize: '14px' }}>
            No calendar events have been created yet. Process emails with meeting information to create calendar events.
          </Typography>
        </Box>
      );
    }

    return (
      <Box sx={{ border: `1px solid ${notionColors.border.default}`, borderRadius: '3px', p: 3 }}>
        <Typography variant="h6" sx={{ mb: 3 }}>
          All Calendar Events ({allEvents.length})
        </Typography>
        <TableContainer sx={{ width: '100%' }}>
          <Table sx={{ width: '100%' }}>
            <TableHead>
              <TableRow>
                <TableCell>Event</TableCell>
                <TableCell>Location</TableCell>
                <TableCell>Start Time</TableCell>
                <TableCell>End Time</TableCell>
                <TableCell>From Email</TableCell>
                <TableCell>Action</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {allEvents.map((event) => (
                <TableRow key={event.id}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <EventIcon sx={{ fontSize: 18, color: notionColors.text.secondary }} />
                      <Typography variant="body2" sx={{ fontSize: '14px' }}>
                        {event.summary || 'Meeting'}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontSize: '14px', color: notionColors.text.secondary }}>
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
                    <Typography variant="body2" sx={{ fontSize: '14px', color: notionColors.text.secondary }}>
                      {event.email_sender || 'Unknown'}
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
                      sx={{
                        fontSize: '12px',
                        px: 1.5,
                        py: 0.5,
                      }}
                    >
                      Open
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    );
  }

  // Handle newly created events view
  if (!results || !results.calendar_events || results.calendar_events.length === 0) {
    return null;
  }

  return (
    <Box sx={{ mt: 4, border: `1px solid ${notionColors.border.default}`, borderRadius: '3px', p: 3 }}>
      <Typography variant="h6" sx={{ mb: 3 }}>
        Created Calendar Events
          </Typography>
      <TableContainer sx={{ width: '100%' }}>
        <Table sx={{ width: '100%' }}>
          <TableHead>
            <TableRow>
              <TableCell>Event</TableCell>
              <TableCell>Location</TableCell>
              <TableCell>Time</TableCell>
              <TableCell>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {results.calendar_events.map((event, idx) => (
              <TableRow key={idx}>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <EventIcon sx={{ fontSize: 18, color: notionColors.text.secondary }} />
          <Typography variant="body2" sx={{ fontSize: '14px' }}>
                      {event.summary || 'Meeting'}
          </Typography>
        </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ fontSize: '14px', color: notionColors.text.secondary }}>
                    {event.location || '—'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ fontSize: '14px', color: notionColors.text.secondary }}>
                    {event.start ? new Date(event.start).toLocaleString() : '—'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Button
                    component="a"
                    href={event.htmlLink}
                    target="_blank"
                    rel="noopener"
                    size="small"
                    startIcon={<OpenInNewIcon sx={{ fontSize: 14 }} />}
                    variant="outlined"
                    sx={{
                      fontSize: '12px',
                      px: 1.5,
                      py: 0.5,
                    }}
                  >
                    Open
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

