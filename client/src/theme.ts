import { createTheme } from '@mui/material/styles';

// Modern blue and white business presentation color palette
export const notionColors = {
  // Primary colors - sophisticated blue palette for business presentation
  primary: {
    main: '#2563EB', // Professional blue
    light: '#60A5FA', // Lighter blue for accents
    dark: '#1E40AF', // Darker blue for depth
    contrast: '#FFFFFF',
    gradient: 'linear-gradient(135deg, #2563EB 0%, #1E40AF 100%)',
    lightGradient: 'linear-gradient(135deg, #60A5FA 0%, #3B82F6 100%)',
  },
  // Text colors - refined for readability
  text: {
    primary: '#0F172A', // Deep slate for headings
    secondary: '#1E293B', // Darker slate for body - better contrast
    tertiary: '#475569', // Medium slate for hints - better contrast
    disabled: '#CBD5E1',
  },
  // Background colors - clean whites with subtle tints
  background: {
    default: '#FFFFFF',
    paper: '#FFFFFF',
    subtle: '#F8FAFC', // Very light blue-gray tint
    hover: 'rgba(37, 99, 235, 0.08)',
    hoverLight: 'rgba(37, 99, 235, 0.04)',
    button: '#2563EB',
    buttonHover: '#1E40AF',
    buttonDisabled: '#CBD5E1',
    gradient: 'linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%)',
  },
  // Border colors - refined and subtle
  border: {
    default: '#94A3B8',
    hover: '#64748B',
    focus: '#2563EB',
    light: '#CBD5E1',
  },
  // Chip colors - modern and clean
  chip: {
    default: 'rgba(37, 99, 235, 0.1)',
    text: '#2563EB',
    success: '#D1FAE5',
    successText: '#059669',
  },
  // Error colors
  error: {
    background: '#FEE2E2',
    text: '#DC2626',
    border: '#FECACA',
  },
  // Warning colors
  warning: {
    background: '#FFF4E5',
    text: '#B7791F',
    main: '#F5A623',
    dark: '#D68910',
  },
  // Shadow - refined for modern presentation style
  shadow: {
    dialog: '0px 20px 25px -5px rgba(0, 0, 0, 0.1), 0px 10px 10px -5px rgba(0, 0, 0, 0.04)',
    card: '0px 4px 6px -1px rgba(0, 0, 0, 0.1), 0px 2px 4px -1px rgba(0, 0, 0, 0.06)',
    button: '0px 4px 14px 0px rgba(37, 99, 235, 0.25)',
    buttonHover: '0px 6px 20px 0px rgba(37, 99, 235, 0.3)',
    subtle: '0px 1px 3px 0px rgba(0, 0, 0, 0.1), 0px 1px 2px 0px rgba(0, 0, 0, 0.06)',
  },
};

export const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: notionColors.primary.main,
      light: notionColors.primary.light,
      dark: notionColors.primary.dark,
      contrastText: notionColors.primary.contrast,
    },
    background: {
      default: notionColors.background.default,
      paper: notionColors.background.paper,
    },
    text: {
      primary: notionColors.text.primary,
      secondary: notionColors.text.secondary,
    },
  },
  typography: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif',
    h1: {
      fontWeight: 700,
      fontSize: '48px',
      lineHeight: 1.1,
      letterSpacing: '-0.03em',
      color: notionColors.text.primary,
    },
    h2: {
      fontWeight: 600,
      fontSize: '36px',
      lineHeight: 1.2,
      letterSpacing: '-0.02em',
      color: notionColors.text.primary,
    },
    h3: {
      fontWeight: 600,
      fontSize: '28px',
      lineHeight: 1.3,
      letterSpacing: '-0.01em',
      color: notionColors.text.primary,
    },
    h4: {
      fontWeight: 600,
      fontSize: '22px',
      lineHeight: 1.4,
      letterSpacing: '-0.01em',
      color: notionColors.text.primary,
    },
    h5: {
      fontWeight: 600,
      fontSize: '18px',
      lineHeight: 1.5,
      color: notionColors.text.primary,
    },
    h6: {
      fontWeight: 600,
      fontSize: '16px',
      lineHeight: 1.5,
      color: notionColors.text.primary,
    },
    body1: {
      fontSize: '16px',
      lineHeight: 1.7,
      color: notionColors.text.secondary,
    },
    body2: {
      fontSize: '14px',
      lineHeight: 1.6,
      color: notionColors.text.secondary,
    },
    button: {
      textTransform: 'none',
      fontSize: '15px',
      fontWeight: 500,
      letterSpacing: '0.01em',
    },
  },
  shape: {
    borderRadius: 0,
  },
  components: {
    MuiButton: {
      defaultProps: {
        disableRipple: true,
      },
      styleOverrides: {
        root: {
          borderRadius: 0,
          textTransform: 'none',
          fontSize: '15px',
          fontWeight: 500,
          padding: '10px 24px',
          transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        },
        contained: {
          backgroundColor: notionColors.primary.main,
          color: 'white',
          boxShadow: 'none',
          fontWeight: 500,
          transition: 'background-color 0.2s cubic-bezier(0.4, 0, 0.2, 1), transform 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            backgroundColor: notionColors.primary.dark,
            boxShadow: 'none',
            transform: 'translateY(-2px)',
          },
          '&:disabled': {
            backgroundColor: notionColors.background.buttonDisabled,
            boxShadow: 'none',
            transform: 'none',
          },
        },
        outlined: {
          borderColor: notionColors.border.default,
          color: notionColors.text.primary,
          borderWidth: '1.5px',
          '&:hover': {
            borderColor: notionColors.primary.main,
            backgroundColor: notionColors.background.hoverLight,
            borderWidth: '1.5px',
          },
        },
        text: {
          color: notionColors.text.secondary,
          '&:hover': {
            backgroundColor: notionColors.background.hover,
            color: notionColors.text.primary,
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 0,
            backgroundColor: '#FFFFFF',
            '& fieldset': {
              borderColor: notionColors.border.default,
              borderWidth: '1.5px',
            },
            '&:hover fieldset': {
              borderColor: notionColors.border.hover,
            },
            '&.Mui-focused fieldset': {
              borderColor: notionColors.primary.main,
              borderWidth: '2px',
            },
            '& input': {
              fontSize: '15px',
              padding: '12px 14px',
            },
            '& textarea': {
              fontSize: '15px',
              padding: '12px 14px',
            },
            '& .MuiSelect-select': {
              fontSize: '15px',
              padding: '12px 14px',
            },
          },
          '& .MuiInputLabel-root': {
            color: notionColors.text.secondary,
            fontSize: '14px',
            fontWeight: 500,
          },
          '& .MuiFormHelperText-root': {
            color: notionColors.text.tertiary,
            fontSize: '12px',
            marginTop: '6px',
          },
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          fontSize: '14px',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontSize: '12px',
          height: '24px',
          border: 'none',
          fontWeight: 500,
        },
      },
    },
    MuiTab: {
      defaultProps: {
        disableRipple: true,
      },
    },
    MuiTabs: {
      styleOverrides: {
        root: {
          '& .MuiTab-root': {
            textTransform: 'none',
            fontSize: '15px',
            fontWeight: 500,
            color: notionColors.text.secondary,
            minHeight: 48,
            padding: '12px 20px',
            '&.Mui-selected': {
              color: notionColors.primary.main,
              fontWeight: 600,
            },
          },
          '& .MuiTabs-indicator': {
            backgroundColor: notionColors.primary.main,
            height: '3px',
            borderRadius: 0,
          },
        },
      },
    },
    MuiTable: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-root': {
            borderColor: notionColors.border.default,
          },
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: notionColors.background.hoverLight,
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          color: notionColors.text.secondary,
          fontSize: '12px',
          fontWeight: 500,
          padding: '12px 16px',
        },
        body: {
          fontSize: '14px',
          color: notionColors.text.primary,
          padding: '12px 16px',
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 0,
          boxShadow: notionColors.shadow.dialog,
          border: `1px solid ${notionColors.border.light}`,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 0,
          boxShadow: notionColors.shadow.card,
          border: `1px solid ${notionColors.border.light}`,
        },
        elevation1: {
          boxShadow: notionColors.shadow.card,
        },
        elevation2: {
          boxShadow: notionColors.shadow.dialog,
        },
      },
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: {
          paddingBottom: '8px',
          borderBottom: `1px solid ${notionColors.border.default}`,
        },
      },
    },
    MuiDialogActions: {
      styleOverrides: {
        root: {
          padding: '16px 24px',
          borderTop: `1px solid ${notionColors.border.default}`,
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 0,
          '&.MuiAlert-error': {
            backgroundColor: notionColors.error.background,
            color: notionColors.error.text,
            border: `1px solid ${notionColors.error.border}`,
            '& .MuiAlert-icon': {
              color: notionColors.error.text,
            },
          },
          '&.MuiAlert-success': {
            backgroundColor: notionColors.chip.success,
            color: notionColors.chip.successText,
            border: `1px solid ${notionColors.chip.success}`,
          },
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          color: notionColors.text.secondary,
          '&:hover': {
            backgroundColor: notionColors.background.hover,
          },
        },
      },
    },
    MuiCircularProgress: {
      styleOverrides: {
        root: {
          color: notionColors.text.secondary,
        },
      },
    },
  },
});

