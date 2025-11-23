import { Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Email as EmailIcon} from '@mui/icons-material';
import { api } from '../api';
import { notionColors } from '../theme';

interface NavbarProps {
  authenticated: boolean;
  onAuthChange: () => void;
}

export default function Navbar({ authenticated, onAuthChange }: NavbarProps) {
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
          {authenticated ? (
              <Button
                onClick={handleLogout}
              variant="text"
              >
                Logout
              </Button>
          ) : (
            <Button
              onClick={() => api.authorize()}
              variant="contained"
            >
              Connect
            </Button>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
}

