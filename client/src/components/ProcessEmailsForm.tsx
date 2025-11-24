import {
  Box,
  Button,
  CircularProgress,
} from '@mui/material';
import {
  Download as DownloadIcon,
} from '@mui/icons-material';
import type { FetchEmailsParams } from '../api';
import MaxEmails from './filter-inputs/MaxEmails';
import TimeWindow from './filter-inputs/TimeWindow';
import CustomQuery from './filter-inputs/CustomQuery';

interface ProcessEmailsFormProps {
  formData: FetchEmailsParams;
  onFormDataChange: (data: FetchEmailsParams) => void;
  onSubmit: (e: React.FormEvent) => Promise<void>;
  loading: boolean;
}

export default function ProcessEmailsForm({
  formData,
  onFormDataChange,
  onSubmit,
  loading,
}: ProcessEmailsFormProps) {
  return (
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
            px: 2.5,
            py: 1,
          }}
        >
          {loading ? 'Processing...' : 'Process Emails'}
        </Button>
      </Box>
    </Box>
  );
}

