import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import { ThemeProvider, CssBaseline, CircularProgress, Box } from '@mui/material';
import { useAuth } from './hooks';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Converter from './pages/Converter';
import Settings from './pages/Settings';
import { theme, notionColors } from './theme';

function App() {
  const { authenticated, loading, checkAuth } = useAuth();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (loading || authenticated === null) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
          <CircularProgress />
        </Box>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <Box sx={{ minHeight: '100vh', backgroundColor: notionColors.background.default, pb: 6 }}>
          <Navbar authenticated={authenticated} onAuthChange={checkAuth} />
          <Box sx={{ maxWidth: '900px', width: '100%', mx: 'auto' }}>
            <Routes>
              <Route path="/" element={<Home authenticated={authenticated} />} />
              <Route path="/converter" element={<Converter authenticated={authenticated} />} />
              <Route path="/settings" element={<Settings authenticated={authenticated} />} />
              <Route path="*" element={<Home authenticated={authenticated} />} />
            </Routes>
          </Box>
        </Box>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
