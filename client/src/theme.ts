import { createTheme } from '@mui/material/styles';

// Modern, refined color palette
export const notionColors = {
  // Primary colors - blue palette from SVG image
  primary: {
    main: '#30A8FF', // Bright blue from SVG
    light: '#88C0FF', // Medium-light blue from SVG
    dark: '#2B7BC5', // Medium-dark blue from SVG
    contrast: '#FFFFFF',
  },
  // Text colors
  text: {
    primary: '#1F2937',
    secondary: '#6B7280',
    tertiary: '#9CA3AF',
    disabled: '#D1D5DB',
  },
  // Background colors
  background: {
    default: '#FFFFFF',
    paper: '#FFFFFF',
    hover: 'rgba(48, 168, 255, 0.06)',
    hoverLight: 'rgba(48, 168, 255, 0.03)',
    button: '#30A8FF',
    buttonHover: '#2B7BC5',
    buttonDisabled: '#D1D5DB',
  },
  // Border colors
  border: {
    default: '#E5E7EB',
    hover: '#D1D5DB',
    focus: '#30A8FF',
  },
  // Chip colors
  chip: {
    default: 'rgba(48, 168, 255, 0.08)',
    text: '#30A8FF',
    success: '#D1FAE5',
    successText: '#059669',
  },
  // Error colors
  error: {
    background: '#FEE2E2',
    text: '#DC2626',
    border: '#FECACA',
  },
  // Shadow
  shadow: {
    dialog: 'rgba(0, 0, 0, 0.1) 0px 0px 0px 1px, rgba(0, 0, 0, 0.05) 0px 3px 6px, rgba(0, 0, 0, 0.1) 0px 9px 24px',
    card: 'rgba(0, 0, 0, 0.04) 0px 2px 8px, rgba(0, 0, 0, 0.02) 0px 1px 3px',
    button: 'rgba(48, 168, 255, 0.2) 0px 4px 12px',
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
    fontFamily: 'ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, "Apple Color Emoji", Arial, sans-serif, "Segoe UI Emoji", "Segoe UI Symbol"',
    h1: {
      fontWeight: 700,
      fontSize: '48px',
      lineHeight: 1.2,
      letterSpacing: '-0.02em',
      color: notionColors.text.primary,
    },
    h2: {
      fontWeight: 600,
      fontSize: '32px',
      letterSpacing: '-0.01em',
      color: notionColors.text.primary,
    },
    h3: {
      fontWeight: 600,
      fontSize: '24px',
      letterSpacing: '-0.01em',
      color: notionColors.text.primary,
    },
    h4: {
      fontWeight: 600,
      fontSize: '20px',
      color: notionColors.text.primary,
    },
    h5: {
      fontWeight: 600,
      fontSize: '18px',
      color: notionColors.text.primary,
    },
    h6: {
      fontWeight: 600,
      fontSize: '16px',
      color: notionColors.text.primary,
    },
    body1: {
      fontSize: '18px',
      lineHeight: 1.6,
      color: notionColors.text.secondary,
    },
    body2: {
      fontSize: '14px',
      color: notionColors.text.secondary,
    },
    button: {
      textTransform: 'none',
      fontSize: '14px',
      fontWeight: 400,
    },
  },
  shape: {
    borderRadius: 3,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '3px',
          textTransform: 'none',
          fontSize: '14px',
          fontWeight: 400,
          transition: 'all 0.2s',
        },
        contained: {
          backgroundColor: notionColors.background.button,
          color: 'white',
          boxShadow: notionColors.shadow.button,
          fontWeight: 500,
          '&:hover': {
            backgroundColor: notionColors.background.buttonHover,
            boxShadow: notionColors.shadow.button,
            transform: 'translateY(-1px)',
          },
          '&:disabled': {
            backgroundColor: notionColors.background.buttonDisabled,
            boxShadow: 'none',
          },
        },
        text: {
          color: notionColors.text.secondary,
          '&:hover': {
            backgroundColor: notionColors.background.hover,
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: '3px',
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
              fontSize: '14px',
            },
            '& textarea': {
              fontSize: '14px',
            },
            '& .MuiSelect-select': {
              fontSize: '14px',
            },
          },
          '& .MuiInputLabel-root': {
            color: notionColors.text.secondary,
            fontSize: '14px',
          },
          '& .MuiFormHelperText-root': {
            color: notionColors.text.tertiary,
            fontSize: '12px',
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
    MuiTabs: {
      styleOverrides: {
        root: {
          '& .MuiTab-root': {
            textTransform: 'none',
            fontSize: '14px',
            fontWeight: 400,
            color: notionColors.text.secondary,
            minHeight: 40,
            '&.Mui-selected': {
              color: notionColors.text.primary,
            },
          },
          '& .MuiTabs-indicator': {
            backgroundColor: notionColors.primary.main,
            height: '3px',
            borderRadius: '3px 3px 0 0',
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
          borderRadius: '8px',
          boxShadow: notionColors.shadow.dialog,
          border: `1px solid ${notionColors.border.default}`,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: '8px',
          boxShadow: notionColors.shadow.card,
        },
        elevation1: {
          boxShadow: notionColors.shadow.card,
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
          borderRadius: '3px',
          '&.MuiAlert-error': {
            backgroundColor: notionColors.error.background,
            color: notionColors.error.text,
            border: `1px solid ${notionColors.error.border}`,
            '& .MuiAlert-icon': {
              color: notionColors.error.text,
            },
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

