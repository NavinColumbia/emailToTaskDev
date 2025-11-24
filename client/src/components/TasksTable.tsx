import { Box, Typography, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, Button } from '@mui/material';
import { CheckCircle as CheckCircleIcon, OpenInNew as OpenInNewIcon } from '@mui/icons-material';
import { notionColors } from '../theme';
import type { FetchEmailsResponse, Task } from '../api';

interface TasksTableProps {
  results?: FetchEmailsResponse;
  allTasks?: Task[];
  loading?: boolean;
}

export default function TasksTable({ results, allTasks, loading }: TasksTableProps) {
  // Handle all tasks view
  if (allTasks !== undefined) {
    if (loading) {
      return (
        <Box sx={{ textAlign: 'center', py: 6 }}>
          <Typography variant="body1" sx={{ color: notionColors.text.secondary }}>
            Loading tasks...
          </Typography>
        </Box>
      );
    }

    if (allTasks.length === 0) {
      return (
        <Box sx={{ border: `1px solid ${notionColors.border.default}`, borderRadius: '3px', p: 6, textAlign: 'center' }}>
          <Typography variant="h6" sx={{ mb: 1, fontSize: '16px', fontWeight: 500 }}>
            No Tasks Found
          </Typography>
          <Typography variant="body2" sx={{ fontSize: '14px' }}>
            No tasks have been processed yet. Start by processing emails from your Gmail account.
          </Typography>
        </Box>
      );
    }

  return (
      <Box sx={{ border: `1px solid ${notionColors.border.default}`, borderRadius: '3px', p: 3 }}>
        <Typography variant="h6" sx={{ mb: 3 }}>
          All Tasks ({allTasks.length})
        </Typography>
        <TableContainer sx={{ width: '100%' }}>
          <Table sx={{ width: '100%' }}>
            <TableHead>
              <TableRow>
                <TableCell>Title</TableCell>
                <TableCell>Sender</TableCell>
                <TableCell>Provider</TableCell>
                <TableCell>Due Date</TableCell>
                <TableCell>Action</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {allTasks.map((task) => (
                <TableRow key={task.id}>
                  <TableCell>
                    <Typography variant="body2" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '14px' }}>
                      {task.task_title || task.email_subject || '(no title)'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontSize: '14px', color: notionColors.text.secondary }}>
                      {task.email_sender || 'Unknown'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={task.provider} 
                      size="small"
                      sx={{ 
                        backgroundColor: notionColors.chip.default,
                        color: notionColors.chip.text,
                      }} 
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontSize: '14px', color: notionColors.text.secondary }}>
                      {task.task_due || '—'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                      <Button
                        component="a"
                      href={task.task_link || "https://tasks.google.com/"}
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

  // Handle newly created tasks view
  if (!results || !results.created || results.created.length === 0) {
    return null;
  }

  return (
    <Box sx={{ mt: 4, border: `1px solid ${notionColors.border.default}`, borderRadius: '3px', p: 3 }}>
      <Typography variant="h6" sx={{ mb: 3 }}>
        Created Tasks
          </Typography>
      <TableContainer sx={{ width: '100%' }}>
        <Table sx={{ width: '100%' }}>
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
                  <Typography variant="body2" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '14px' }}>
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

