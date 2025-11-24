import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, Button } from '@mui/material';
import { CheckCircle as CheckCircleIcon, OpenInNew as OpenInNewIcon } from '@mui/icons-material';
import { notionColors } from '../theme';
import type { FetchEmailsResponse } from '../api';

interface NewTasksTableProps {
  results: FetchEmailsResponse;
}

export default function NewTasksTable({ results }: NewTasksTableProps) {
  if (!results.created || results.created.length === 0) {
    return null;
  }

  return (
    <Box sx={{ mt: 4, border: `1px solid ${notionColors.border.default}`, borderRadius: '3px', p: 3 }}>
      <Typography variant="h6" sx={{ mb: 3 }}>
        Created Tasks
      </Typography>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Title</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {results.created.map((item, idx) => (
              <TableRow key={idx}>
                <TableCell>
                  <Typography variant="body2" sx={{ maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '14px' }}>
                    {item.task.title || '(no title)'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    icon={<CheckCircleIcon sx={{ fontSize: 14, color: notionColors.chip.successText }} />}
                    label={item.task.due ? `Created · due ${item.task.due}` : 'Created'}
                    size="small"
                    sx={{
                      backgroundColor: notionColors.chip.success,
                      color: notionColors.chip.successText,
                    }}
                  />
                </TableCell>
                <TableCell>
                  <Button
                    component="a"
                    href={item.task.webLink || "https://tasks.google.com/"}
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

