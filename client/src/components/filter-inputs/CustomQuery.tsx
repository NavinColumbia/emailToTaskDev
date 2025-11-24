import { TextField } from '@mui/material';

interface CustomQueryProps {
  value: string;
  onChange: (value: string) => void;
  label?: string;
  placeholder?: string;
  helperText?: string;
  disabled?: boolean;
  fullWidth?: boolean;
  sx?: object;
}

export default function CustomQuery({
  value,
  onChange,
  label = 'Custom Gmail Query',
  placeholder = 'e.g., from:boss@example.com has:attachment',
  helperText = 'Overrides other filters',
  disabled = false,
  fullWidth = false,
  sx,
}: CustomQueryProps) {
  return (
    <TextField
      type="text"
      label={label}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      helperText={helperText}
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

