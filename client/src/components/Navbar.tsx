import { memo } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Email as EmailIcon, Settings as SettingsIcon, AutoAwesome as ConverterIcon, Logout as LogoutIcon } from '@mui/icons-material';
import { api } from '../apis/api';
import { notionColors } from '../theme';

interface NavbarProps {
  authenticated: boolean;
  onAuthChange: () => void;
}

function Navbar({ authenticated, onAuthChange }: NavbarProps) {
  const location = useLocation();
  const isHome = location.pathname === '/';

  const handleLogout = async () => {
    await api.logout();
    onAuthChange();
  };

  return (
    <AppBar 
      position="sticky" 
      elevation={0}
      sx={{ 
        mb: 3,
        backgroundColor: isHome ? 'transparent' : '#FFFFFF',
        color: isHome ? '#FFFFFF' : 'text.primary',
        border: 'none',
        boxShadow: isHome ? 'none' : undefined,
      }}
    >
      <Toolbar sx={{ width: '100%', px: 3, py: 2, minHeight: '64px !important' }}>
        <Box 
          component={Link} 
          to="/" 
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 1.5, 
            textDecoration: 'none', 
            color: isHome ? '#FFFFFF' : notionColors.text.primary,
            '&:hover': { opacity: 0.7 },
            transition: 'opacity 0.2s',
          }}
        >
          <EmailIcon sx={{ fontSize: 22, color: isHome ? '#FFFFFF' : notionColors.primary.main }} />
          <Typography 
            variant="h6" 
            component="div" 
            sx={{ 
              fontWeight: 700,
              fontSize: '24px',
              letterSpacing: '-0.02em',
              ...(isHome ? {
                color: '#FFFFFF',
              } : {
                background: notionColors.primary.gradient,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }),
            }}
          >
            Taskflow
          </Typography>
        </Box>
        <Box sx={{ flexGrow: 1 }} />
        {authenticated && (
          <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'center' }}>
            <Button
              component={Link}
              to="/converter"
              variant="text"
              startIcon={<ConverterIcon sx={{ fontSize: 18, color: isHome ? '#FFFFFF' : 'inherit' }} />}
              sx={{ 
                fontSize: '14px',
                px: 2,
                py: 0.75,
                borderRadius: 0,
                minWidth: 'auto',
                textTransform: 'none',
                color: isHome ? '#FFFFFF' : 'inherit',
                '&:hover': {
                  backgroundColor: isHome ? 'rgba(255, 255, 255, 0.1)' : undefined,
                  color: isHome ? '#FFFFFF' : undefined,
                },
              }}
            >
              Converter
            </Button>
            <Button
              component={Link}
              to="/settings"
              variant="text"
              startIcon={<SettingsIcon sx={{ fontSize: 18, color: isHome ? '#FFFFFF' : 'inherit' }} />}
              sx={{ 
                fontSize: '14px',
                px: 2,
                py: 0.75,
                borderRadius: 0,
                minWidth: 'auto',
                textTransform: 'none',
                color: isHome ? '#FFFFFF' : 'inherit',
                '&:hover': {
                  backgroundColor: isHome ? 'rgba(255, 255, 255, 0.1)' : undefined,
                  color: isHome ? '#FFFFFF' : undefined,
                },
              }}
            >
              Settings
            </Button>
            <Button
              onClick={handleLogout}
              variant="text"
              startIcon={<LogoutIcon sx={{ fontSize: 18, color: isHome ? '#FFFFFF' : 'inherit' }} />}
              sx={{ 
                fontSize: '14px',
                px: 2,
                py: 0.75,
                borderRadius: 0,
                minWidth: 'auto',
                textTransform: 'none',
                color: isHome ? '#FFFFFF' : 'inherit',
                '&:hover': {
                  backgroundColor: isHome ? 'rgba(255, 255, 255, 0.1)' : undefined,
                  color: isHome ? '#FFFFFF' : undefined,
                },
              }}
            >
              Logout
            </Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
}

export default memo(Navbar);

