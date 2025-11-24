import { Box, Button, Typography } from '@mui/material';
import { Google as GoogleIcon } from '@mui/icons-material';
import { Link } from 'react-router-dom';
import { api } from '../api';
import { notionColors } from '../theme';

interface HomeProps {
  authenticated: boolean;
}

export default function Home({ authenticated }: HomeProps) {
  if (!authenticated) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
        <Box sx={{ textAlign: 'center', maxWidth: 600, px: 3 }}>
          <Typography 
            variant="h1" 
            component="h1" 
            sx={{ 
              fontWeight: 700,
              fontSize: '48px',
              lineHeight: 1.2,
              mb: 2,
              letterSpacing: '-0.02em',
            }}
          >
            Taskflow
          </Typography>
          <Typography 
            variant="body1" 
            sx={{ 
              fontSize: '18px',
              mb: 4,
              lineHeight: 1.6,
            }}
          >
            Convert Gmail emails to tasks automatically using AI-powered classification
          </Typography>
          <Button
            onClick={() => api.authorize()}
            variant="contained"
            startIcon={<GoogleIcon />}
            sx={{ 
              fontSize: '15px',
              px: 3,
              py: 1.25,
            }}
          >
            Connect with Google
          </Button>
        </Box>
      </Box>
    );
  }

    return (
    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
      <Box sx={{ textAlign: 'center', maxWidth: 600, px: 3 }}>
        <Typography 
          variant="h1" 
          component="h1" 
          sx={{ 
            fontWeight: 700,
            fontSize: '48px',
            lineHeight: 1.2,
            mb: 2,
            letterSpacing: '-0.02em',
          }}
        >
          Welcome to Taskflow
        </Typography>
        <Typography 
          variant="body1" 
          sx={{ 
            fontSize: '18px',
            mb: 4,
            lineHeight: 1.6,
            color: notionColors.text.secondary,
          }}
        >
          Convert Gmail emails to tasks automatically using AI-powered classification
        </Typography>
        <Button
          component={Link}
          to="/converter"
          variant="contained"
          sx={{ 
            fontSize: '15px',
            px: 3,
            py: 1.25,
          }}
        >
          Get Started
        </Button>
      </Box>
    </Box>
    );
  }
