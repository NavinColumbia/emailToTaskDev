import { Box, Button, Typography } from '@mui/material';
import { Link } from 'react-router-dom';
import { notionColors } from '../theme';
import productivityImage from '../assets/image.svg';

interface HomeProps {
  authenticated: boolean;
}

export default function Home({ authenticated }: HomeProps) {
  if (!authenticated) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '80vh', gap: 3 }}>
        <Box
          component="img"
          src={productivityImage}
          alt="Productivity and time management"
          sx={{
            maxWidth: '100%',
            width: '250px',
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
              lineHeight: 1.2,
              mb: 2,
              letterSpacing: '-0.02em',
              color: notionColors.primary.main,
            }}
          >
            Taskflow
          </Typography>
          <Typography 
            variant="body1" 
            sx={{ 
              fontSize: '18px',
              lineHeight: 1.6,
              color: notionColors.text.secondary,
            }}
          >
            Convert Gmail emails to tasks automatically using AI-powered classification
          </Typography>
        </Box>
      </Box>
    );
  }

    return (
    <Box sx={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '80vh', gap: 3 }}>
      <Box
        component="img"
        src={productivityImage}
        alt="Productivity and time management"
        sx={{
          maxWidth: '100%',
          width: '250px',
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
            lineHeight: 1.2,
            mb: 2,
            letterSpacing: '-0.02em',
            color: notionColors.primary.main,
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
            px: 4,
            py: 1.5,
            borderRadius: '8px',
          }}
        >
          Get Started
        </Button>
      </Box>
    </Box>
    );
  }
