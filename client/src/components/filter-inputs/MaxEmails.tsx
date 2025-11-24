import { TextField } from '@mui/material';

interface MaxEmailsProps {
  value: number | undefined;
  onChange: (value: number | undefined) => void;
  label?: string;
  placeholder?: string;
  helperText?: string;
  disabled?: boolean;
  fullWidth?: boolean;
  sx?: object;
}

export default function MaxEmails({
  value,
  onChange,
  label = 'Max Emails',
  placeholder = 'All',
  helperText,
  disabled = false,
  fullWidth = false,
  sx,
}: MaxEmailsProps) {
  return (
    <TextField
      type="number"
      label={label}
      value={value || ''}
      onChange={(e) => onChange(e.target.value ? Number(e.target.value) : undefined)}
      placeholder={placeholder}
      helperText={helperText}
      slotProps={{ htmlInput: { min: 1 } }}
      fullWidth={fullWidth}
      disabled={disabled}
      sx={{
        flex: fullWidth ? undefined : 1,
        '& .MuiInputBase-input': {
          height: '56px',
          boxSizing: 'border-box'
        },
        ...sx,
      }}
    />
  );
}

