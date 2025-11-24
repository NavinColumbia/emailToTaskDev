import {
  Box,
  TextField,
  MenuItem,
  Button,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
} from '@mui/material';
import {
  Download as DownloadIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { notionColors } from '../theme';
import type { FetchEmailsParams } from '../api';

interface ProcessEmailsFormProps {
  formData: FetchEmailsParams;
  onFormDataChange: (data: FetchEmailsParams) => void;
  onSubmit: (e: React.FormEvent) => Promise<void>;
  loading: boolean;
  error: string | null;
}

export default function ProcessEmailsForm({
  formData,
  onFormDataChange,
  onSubmit,
  loading,
  error,
}: ProcessEmailsFormProps) {
  return (
    <Box component="form" onSubmit={onSubmit}>
      <Box sx={{ display: 'flex', gap: 2, mb: 3, alignItems: 'center', width: '100%' }}>
        <TextField
          type="number"
          label="Max Emails"
          value={formData.max || ''}
          onChange={(e) => onFormDataChange({ ...formData, max: e.target.value ? Number(e.target.value) : undefined })}
          placeholder="All"
          slotProps={{ htmlInput: { min: 1 } }}
          sx={{ 
            flex: 1,
            '& .MuiInputBase-input': {
              height: '56px',
              boxSizing: 'border-box'
            }
          }}
        />

        <TextField
          select
          label="Time Window"
          value={formData.window}
          onChange={(e) => onFormDataChange({ ...formData, window: e.target.value })}
          sx={{ 
            flex: 1,
            '& .MuiInputBase-input': {
              height: '56px',
              boxSizing: 'border-box'
            }
          }}
        >
          <MenuItem value="">All emails</MenuItem>
          <MenuItem value="1d">Last 24 hours</MenuItem>
          <MenuItem value="7d">Last 7 days</MenuItem>
          <MenuItem value="30d">Last 30 days</MenuItem>
        </TextField>

        <TextField
          select
          label="Dry Run"
          value={formData.dry_run ? 'true' : 'false'}
          onChange={(e) => onFormDataChange({ ...formData, dry_run: e.target.value === 'true' })}
          sx={{ 
            flex: 1,
            '& .MuiInputBase-input': {
              height: '56px',
              boxSizing: 'border-box'
            }
          }}
        >
          <MenuItem value="false">No</MenuItem>
          <MenuItem value="true">Yes</MenuItem>
        </TextField>
      </Box>

      <Accordion elevation={0}>
        <AccordionSummary 
          expandIcon={<ExpandMoreIcon sx={{ fontSize: 18, color: notionColors.text.secondary }} />}
        >
          <Typography variant="body2" sx={{ fontSize: '14px' }}>
            Advanced Options
          </Typography>
        </AccordionSummary>
        <AccordionDetails sx={{ pt: 0, pb: 2 }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, width: '100%' }}>
            <TextField
              type="number"
              label="Since (hours ago)"
              value={formData.since_hours || ''}
              onChange={(e) => onFormDataChange({ ...formData, since_hours: e.target.value ? Number(e.target.value) : undefined })}
              placeholder="e.g., 24"
              helperText="Precise time filter (overrides time window)"
              fullWidth
              sx={{
                '& .MuiInputBase-input': {
                  height: '56px',
                  boxSizing: 'border-box'
                }
              }}
            />
            <TextField
              type="text"
              label="Since (ISO 8601)"
              value={formData.since}
              onChange={(e) => onFormDataChange({ ...formData, since: e.target.value })}
              placeholder="e.g., 2025-10-27T12:00:00Z"
              helperText="Overrides hours if both provided"
              fullWidth
              sx={{
                '& .MuiInputBase-input': {
                  height: '56px',
                  boxSizing: 'border-box'
                }
              }}
            />
            <TextField
              type="text"
              label="Custom Gmail Query"
              value={formData.q}
              onChange={(e) => onFormDataChange({ ...formData, q: e.target.value })}
              placeholder="e.g., from:boss@example.com has:attachment"
              helperText="Advanced Gmail search query (overrides other filters)"
              fullWidth
              sx={{
                '& .MuiInputBase-input': {
                  height: '56px',
                  boxSizing: 'border-box'
                }
              }}
            />
          </Box>
        </AccordionDetails>
      </Accordion>

      <Box sx={{ mt: 3, display: 'flex', gap: 2, width: '100%' }}>
        <Button
          type="submit"
          variant="contained"
          startIcon={loading ? <CircularProgress size={16} color="inherit" /> : <DownloadIcon sx={{ fontSize: 18 }} />}
          disabled={loading}
          sx={{
            px: 2.5,
            py: 1,
          }}
        >
          {loading ? 'Processing...' : 'Process Emails'}
        </Button>
      </Box>

      {error && (
        <Alert 
          severity="error" 
          sx={{ mt: 3 }}
        >
          {error}
        </Alert>
      )}
    </Box>
  );
}

