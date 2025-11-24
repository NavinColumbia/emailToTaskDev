import { Link, useLocation } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Email as EmailIcon, Settings as SettingsIcon, AutoAwesome as ConverterIcon} from '@mui/icons-material';
import { api } from '../api';
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
        backgroundColor: notionColors.background.default,
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
          <EmailIcon sx={{ fontSize: 20, color: notionColors.text.icon }} />
          <Typography 
            variant="h6" 
            component="div" 
            sx={{ 
              fontWeight: 500,
              fontSize: '16px',
              letterSpacing: '-0.01em',
            }}
          >
            Taskflow
          </Typography>
        </Box>
        <Box sx={{ flexGrow: 1 }} />
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {authenticated && (
            <>
              <Button
                component={Link}
                to="/converter"
                variant="text"
                startIcon={<ConverterIcon />}
                sx={{
                  color: location.pathname === '/converter' ? notionColors.text.primary : notionColors.text.secondary,
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
                  color: location.pathname === '/settings' ? notionColors.text.primary : notionColors.text.secondary,
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
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
}

