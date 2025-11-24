import { useState } from 'react';
import { Box, Typography, Button, CircularProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, IconButton, Tooltip } from '@mui/material';
import { List as ListIcon, Refresh as RefreshIcon, OpenInNew as OpenInNewIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { notionColors } from '../theme';
import { formatDate } from '../utils/dateUtils';
import type { Task } from '../api';

interface TasksTableProps {
  tasks: Task[];
  loading: boolean;
  onRefresh: () => void;
  onDelete: (taskId: number) => Promise<void>;
}

export default function TasksTable({ tasks, loading, onRefresh, onDelete }: TasksTableProps) {
  const [deletingTaskId, setDeletingTaskId] = useState<number | null>(null);

  const handleDelete = async (taskId: number) => {
    if (!confirm('Are you sure you want to delete this task? This will remove it from Google Tasks and cannot be undone.')) {
      return;
    }

    setDeletingTaskId(taskId);
    try {
      await onDelete(taskId);
    } catch (error) {
      console.error('Failed to delete task:', error);
      alert(error instanceof Error ? error.message : 'Failed to delete task');
    } finally {
      setDeletingTaskId(null);
    }
  };
  return (
    <>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" sx={{ fontSize: '16px' }}>
          All Processed Tasks ({tasks.length})
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
      ) : tasks.length > 0 ? (
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Task Title</TableCell>
                <TableCell>Sender</TableCell>
                <TableCell>Provider</TableCell>
                <TableCell>Received</TableCell>
                <TableCell>Processed</TableCell>
                <TableCell>Due</TableCell>
                <TableCell>Action</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tasks.map((task, idx) => (
                <TableRow key={idx}>
                  <TableCell>
                    <Typography
                      variant="body2"
                      sx={{
                        maxWidth: 300,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                        fontSize: '14px',
                      }}
                      title={task.task_title || task.email_subject || 'No title'}
                    >
                      {task.task_title || task.email_subject || 'No title'}
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
                      title={task.email_sender || 'Unknown'}
                    >
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
                    <Typography variant="body2" sx={{ fontSize: '14px' }}>
                      {formatDate(task.email_received_at)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ fontSize: '14px' }}>
                      {formatDate(task.created_at)}
                    </Typography>
                  </TableCell>
                  <TableCell sx={{ fontSize: '14px' }}>{task.task_due ? formatDate(task.task_due) : '—'}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      <Button
                        component="a"
                        href={task.task_link && !task.task_link.includes('googleapis.com') ? task.task_link : "https://tasks.google.com/"}
                        target="_blank"
                        rel="noopener"
                        size="small"
                        startIcon={<OpenInNewIcon sx={{ fontSize: 14 }} />}
                        variant="outlined"
                        sx={{ fontSize: '12px', px: 1.5, py: 0.5 }}
                      >
                        Open
                      </Button>
                      <Tooltip title="Delete task">
                        <IconButton
                          size="small"
                          onClick={() => handleDelete(task.id)}
                          disabled={deletingTaskId === task.id}
                          sx={{ 
                            color: notionColors.text.secondary,
                            '&:hover': {
                              color: 'error.main',
                            }
                          }}
                        >
                          {deletingTaskId === task.id ? (
                            <CircularProgress size={16} />
                          ) : (
                            <DeleteIcon sx={{ fontSize: 18 }} />
                          )}
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Box sx={{ border: `1px solid ${notionColors.border.default}`, borderRadius: '3px', p: 6, textAlign: 'center' }}>
          <ListIcon sx={{ fontSize: 48, color: notionColors.text.disabled, mb: 2 }} />
          <Typography variant="h6" sx={{ mb: 1, fontSize: '16px', fontWeight: 500 }}>
            No Tasks Found
          </Typography>
          <Typography variant="body2" sx={{ fontSize: '14px' }}>
            No tasks have been processed yet. Start by processing emails from your Gmail account.
          </Typography>
        </Box>
      )}
    </>
  );
}

