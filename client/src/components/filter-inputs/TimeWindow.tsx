import { useState } from 'react';
import { TextField, MenuItem, Dialog, DialogTitle, DialogContent, DialogActions, Button } from '@mui/material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs, { type Dayjs } from 'dayjs';
import utc from 'dayjs/plugin/utc';

dayjs.extend(utc);

interface TimeWindowProps {
  value: string;
  onChange: (value: string) => void;
  since?: string;
  onSinceChange?: (since: string | undefined) => void;
  label?: string;
  helperText?: string;
  disabled?: boolean;
  fullWidth?: boolean;
  sx?: object;
  showCustomOption?: boolean;
}

export default function TimeWindow({
  value,
  onChange,
  since,
  onSinceChange,
  label = 'Time Window',
  helperText,
  disabled = false,
  fullWidth = false,
  sx,
  showCustomOption = true,
}: TimeWindowProps) {
  const [datePickerOpen, setDatePickerOpen] = useState(false);
  const [tempDate, setTempDate] = useState<Dayjs | null>(null);

  const handleOpenDatePicker = () => {
    setTempDate(since ? dayjs(since) : null);
    setDatePickerOpen(true);
  };

  const handleDateChange = (newValue: Dayjs | null) => {
    setTempDate(newValue);
  };

  const handleDateConfirm = () => {
    if (tempDate && onSinceChange) {
      onChange('custom');
      onSinceChange(tempDate.utc().toISOString());
    }
    setDatePickerOpen(false);
  };

  const handleDateCancel = () => {
    setTempDate(since ? dayjs(since) : null);
    setDatePickerOpen(false);
  };

  const handleWindowChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newWindow = e.target.value;
    if (newWindow === 'custom') {
      e.preventDefault();
      handleOpenDatePicker();
    } else {
      onChange(newWindow);
    }
  };

  return (
    <>
      <TextField
        select
        label={label}
        value={value === 'custom' && since ? 'custom' : value}
        onChange={handleWindowChange}
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
            '& .MuiSelect-select': {
              display: 'flex',
              alignItems: 'center',
              height: '53px',
              padding: '0px',
            },
          },
          ...sx,
        }}
      >
        <MenuItem value="">All emails</MenuItem>
        <MenuItem value="1d">Last 24 hours</MenuItem>
        <MenuItem value="7d">Last 7 days</MenuItem>
        <MenuItem value="30d">Last 30 days</MenuItem>
        {showCustomOption && (
          <MenuItem 
            value="custom"
            onClick={(e) => {
              e.stopPropagation();
              handleOpenDatePicker();
            }}
          >
            {since ? dayjs(since).format('YYYY-MM-DD HH:mm') : 'Custom'}
          </MenuItem>
        )}
      </TextField>

      {showCustomOption && (
        <Dialog open={datePickerOpen} onClose={handleDateCancel}>
          <DialogTitle>Select Date & Time</DialogTitle>
          <DialogContent>
            <LocalizationProvider dateAdapter={AdapterDayjs}>
              <DateTimePicker
                label="Since (Date & Time)"
                value={tempDate}
                onChange={handleDateChange}
                ampm={false}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    sx: {
                      mt: 2,
                      '& .MuiInputBase-input': {
                        fontSize: '1rem',
                      }
                    }
                  }
                }}
              />
            </LocalizationProvider>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleDateCancel}>Cancel</Button>
            <Button onClick={handleDateConfirm} variant="contained">OK</Button>
          </DialogActions>
        </Dialog>
      )}
    </>
  );
}

