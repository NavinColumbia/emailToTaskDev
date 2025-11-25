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
  placeholder = 'e.g., has:attachment',
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
        '& .MuiOutlinedInput-root': {
          backgroundColor: '#FFFFFF',
          padding: '0px 14px',
          display: 'flex',
          alignItems: 'center',
          '& .MuiInputBase-input': {
            height: '53px',
            padding: '0px',
            boxSizing: 'border-box',
            display: 'flex',
            alignItems: 'center',
          },
        },
        ...sx,
      }}
    />
  );
}

