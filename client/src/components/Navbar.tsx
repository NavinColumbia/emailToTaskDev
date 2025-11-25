import { Link, useLocation } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Email as EmailIcon, Settings as SettingsIcon, AutoAwesome as ConverterIcon, Google as GoogleIcon } from '@mui/icons-material';
import { api } from '../apis/api';
import { notionColors } from '../theme';

interface NavbarProps {
  authenticated: boolean;
  onAuthChange: () => void;
}

export default function Navbar({ authenticated, onAuthChange }: NavbarProps) {
  const location = useLocation();
  const handleLogout = async () => {
    await api.logout();
    onAuthChange();
  };

  return (
    <AppBar 
      position="sticky" 
      elevation={0}
      sx={{ 
        mb: 0,
        backgroundColor: '#FFFFFF',
        color: 'text.primary',
        borderBottom: `1px solid ${notionColors.border.default}`,
      }}
    >
      <Toolbar sx={{ maxWidth: '900px', width: '100%', mx: 'auto', px: 3, py: 1.5, minHeight: '48px !important' }}>
        <Box 
          component={Link} 
          to="/" 
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 1.5, 
            textDecoration: 'none', 
            color: notionColors.text.primary,
            '&:hover': { opacity: 0.7 },
            transition: 'opacity 0.2s',
          }}
        >
          <EmailIcon sx={{ fontSize: 22, color: notionColors.primary.main }} />
          <Typography 
            variant="h6" 
            component="div" 
            sx={{ 
              fontWeight: 600,
              fontSize: '18px',
              letterSpacing: '-0.01em',
              color: notionColors.primary.main,
            }}
          >
            Taskflow
          </Typography>
        </Box>
        <Box sx={{ flexGrow: 1 }} />
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {authenticated ? (
            <>
              <Button
                component={Link}
                to="/converter"
                variant="text"
                startIcon={<ConverterIcon />}
                sx={{
                  color: location.pathname === '/converter' ? notionColors.primary.main : notionColors.text.secondary,
                  '&:hover': {
                    backgroundColor: notionColors.background.hover,
                    color: notionColors.primary.main,
                  },
                }}
              >
                Converter
              </Button>
              <Button
                component={Link}
                to="/settings"
                variant="text"
                startIcon={<SettingsIcon />}
                sx={{
                  color: location.pathname === '/settings' ? notionColors.primary.main : notionColors.text.secondary,
                  '&:hover': {
                    backgroundColor: notionColors.background.hover,
                    color: notionColors.primary.main,
                  },
                }}
              >
                Settings
              </Button>
              <Button
                onClick={handleLogout}
                variant="text"
              >
                Logout
              </Button>
            </>
          ) : (
            <Button
              onClick={() => api.authorize()}
              variant="contained"
              startIcon={<GoogleIcon />}
              sx={{ 
                fontSize: '15px',
                px: 3,
                py: 1,
                borderRadius: '8px',
              }}
            >
              Google Login
            </Button>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
}

