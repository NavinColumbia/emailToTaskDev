import { Box, Button, Typography } from '@mui/material';
import { Link } from 'react-router-dom';
import { Google as GoogleIcon } from '@mui/icons-material';
import { api } from '../apis/api';
import productivityImage from '../assets/image.svg';
import { useAuth } from '../hooks/useAuth';
import { useEffect } from 'react';

interface HomeProps {
  authenticated: boolean;
}

export default function Home({ authenticated }: HomeProps) {
  const { checkAuth } = useAuth();
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', py: 4, gap: 2 }}>
      <Box
        component="img"
        src={productivityImage}
        alt="Productivity and time management"
        sx={{
          maxWidth: '100%',
          width: '300px',
          height: 'auto',
          objectFit: 'contain',
        }}
      />
      <Box sx={{ textAlign: 'center', maxWidth: 600, px: 3 }}>
        <Typography 
          variant="h1" 
          component="h1" 
          sx={{ 
            fontWeight: 700,
            fontSize: '48px',
            lineHeight: 1.1,
            mb: 1.5,
            letterSpacing: '-0.03em',
            color: '#FFFFFF',
          }}
        >
          Welcome to Taskflow
        </Typography>
        <Typography 
          variant="body1" 
          sx={{ 
            fontSize: '16px',
            lineHeight: 1.5,
            color: '#CCCCCC',
            mb: 3,
          }}
        >
          Convert Gmail emails to tasks automatically using AI-powered classification
        </Typography>
        {authenticated ? (
          <Button
            component={Link}
            to="/converter"
            variant="contained"
            sx={{ 
              fontSize: '16px',
              px: 5,
              py: 1.75,
              borderRadius: 0,
              fontWeight: 600,
              textTransform: 'none',
            }}
          >
            Get Started
          </Button>
        ) : (
          <Button
            onClick={() => api.authorize()}
            variant="contained"
            startIcon={<GoogleIcon sx={{ fontSize: 18 }} />}
            sx={{ 
              fontSize: '16px',
              px: 5,
              py: 1.75,
              borderRadius: 0,
              fontWeight: 600,
              textTransform: 'none',
            }}
          >
            Sign in with Google
          </Button>
        )}
      </Box>
    </Box>
  );
}
