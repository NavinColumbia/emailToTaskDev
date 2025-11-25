import {
  Box,
  Button,
  CircularProgress,
  Paper,
} from '@mui/material';
import {
  Download as DownloadIcon,
} from '@mui/icons-material';
import type { FetchEmailsParams } from '../../apis/api';
import { notionColors } from '../../theme';
import MaxEmails from '../filter-inputs/MaxEmails';
import TimeWindow from '../filter-inputs/TimeWindow';
import CustomQuery from '../filter-inputs/CustomQuery';

interface ProcessEmailsProps {
  formData: FetchEmailsParams;
  onFormDataChange: (data: FetchEmailsParams) => void;
  onSubmit: (e: React.FormEvent) => Promise<void>;
  loading: boolean;
}

export default function ProcessEmails({
  formData,
  onFormDataChange,
  onSubmit,
  loading,
}: ProcessEmailsProps) {
  return (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        border: `1.5px solid ${notionColors.border.default}`,
        borderRadius: 3,
        backgroundColor: '#FFFFFF',
        boxShadow: notionColors.shadow.card,
      }}
    >
    <Box component="form" onSubmit={onSubmit}>
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start', width: '100%', flexWrap: 'nowrap', mb: 3 }}>
        <MaxEmails
          value={formData.max}
          onChange={(max) => onFormDataChange({ ...formData, max })}
        />

        <TimeWindow
          value={formData.window || ''}
          onChange={(window) => onFormDataChange({ ...formData, window, since: window !== 'custom' ? undefined : formData.since })}
          since={formData.since}
          onSinceChange={(since) => onFormDataChange({ ...formData, since, window: 'custom' })}
        />

        <CustomQuery
          value={formData.q || ''}
          onChange={(q) => onFormDataChange({ ...formData, q })}
        />
      </Box>

      <Box sx={{ mt: 3, display: 'flex', gap: 2, width: '100%' }}>
        <Button
          type="submit"
          variant="contained"
          startIcon={loading ? <CircularProgress size={16} color="inherit" /> : <DownloadIcon sx={{ fontSize: 18 }} />}
          disabled={loading}
          sx={{
              px: 3,
              py: 1.25,
              borderRadius: '8px',
              fontSize: '14px',
          }}
        >
          {loading ? 'Processing...' : 'Process Emails'}
        </Button>
      </Box>
    </Box>
    </Paper>
  );
}

