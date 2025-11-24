import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Button } from '@mui/material';
import { Event as EventIcon, OpenInNew as OpenInNewIcon } from '@mui/icons-material';
import { notionColors } from '../theme';
import type { FetchEmailsResponse } from '../api';

interface NewEventsTableProps {
  results: FetchEmailsResponse;
}

export default function NewEventsTable({ results }: NewEventsTableProps) {
  if (!results.calendar_events || results.calendar_events.length === 0) {
    return null;
  }

  return (
    <Box sx={{ mt: 4, border: `1px solid ${notionColors.border.default}`, borderRadius: '3px', p: 3 }}>
      <Typography variant="h6" sx={{ mb: 3 }}>
        Created Calendar Events
      </Typography>
      <TableContainer>
        <Table size="small">
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

