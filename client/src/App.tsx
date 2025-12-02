import { BrowserRouter, Routes, Route, useSearchParams, useLocation } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { ThemeProvider, CssBaseline, CircularProgress, Box } from '@mui/material';
import { useAuth } from './hooks';
import { setToken } from './apis/base';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Converter from './pages/Converter';
import Settings from './pages/Settings';
import { theme } from './theme';
import gradientBackground from './assets/gradient-background.png';

function AppContent() {
  const { authenticated, loading, checkAuth } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [initialized, setInitialized] = useState(false);
  const location = useLocation();
  const isHome = location.pathname === '/';

  useEffect(() => {
    // Only check auth once on mount
    if (!initialized) {
      checkAuth();
      setInitialized(true);
    }
  }, [checkAuth, initialized]);

  useEffect(() => {
    // Extract token from URL query param after OAuth redirect
    const token = searchParams.get('token');
    if (token) {
      setToken(token);
      // Remove token from URL
      const newSearchParams = new URLSearchParams(searchParams);
      newSearchParams.delete('token');
      setSearchParams(newSearchParams, { replace: true });
      // Re-check auth after setting token
      checkAuth();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams.toString()]);

  if (loading || authenticated === null) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box 
      sx={{ 
        minHeight: '100vh', 
        pb: 6,
        position: 'relative',
        backgroundColor: isHome ? '#0e0e0e' : '#ffffff',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'fixed',
          top: '-400px',
          right: isHome ? '-200px' : '-400px',
          width: '1000px',
          height: 'auto',
          aspectRatio: '1 / 1',
          backgroundImage: `url(${gradientBackground})`,
          backgroundSize: 'cover',
          backgroundRepeat: 'no-repeat',
          backgroundPosition: 'center',
          transform: 'rotate(60deg)',
          zIndex: 0,
          pointerEvents: 'none',
          opacity: isHome ? 0.4 : 0.2,
        },
        '&::after': {
          content: '""',
          position: 'fixed',
          bottom: '-900px',
          left: '-550px',
          width: '1200px',
          height: 'auto',
          aspectRatio: '1 / 1',
          backgroundImage: `url(${gradientBackground})`,
          backgroundSize: 'cover',
          backgroundRepeat: 'no-repeat',
          backgroundPosition: 'center',
          transform: 'rotate(-60deg)',
          zIndex: 0,
          pointerEvents: 'none',
          opacity: 0.3,
        },
      }}
    >
      <Box sx={{ position: 'relative', zIndex: 1 }}>
        <Navbar authenticated={authenticated} onAuthChange={checkAuth} />
      </Box>
      <Box sx={{ maxWidth: '1200px', width: '100%', mx: 'auto', px: { xs: 2, sm: 3, md: 4 }, pt: 8, position: 'relative', zIndex: 1 }}>
        <Box sx={{ 
          minHeight: 'calc(100vh - 200px)',
          position: 'relative',
        }}>
          <Routes>
            <Route path="/" element={<Home authenticated={authenticated} />} />
            <Route path="/converter" element={<Converter authenticated={authenticated} />} />
            <Route path="/settings" element={<Settings authenticated={authenticated} />} />
            <Route path="*" element={<Home authenticated={authenticated} />} />
          </Routes>
        </Box>
      </Box>
    </Box>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
