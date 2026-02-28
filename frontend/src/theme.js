import { createTheme } from '@mui/material/styles'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary:   { main: '#1565C0', light: '#1E88E5', dark: '#0D47A1' },
    secondary: { main: '#0A2342' },
    success:   { main: '#27AE60' },
    error:     { main: '#E74C3C' },
    warning:   { main: '#F39C12' },
    background: { default: '#F5F7FA', paper: '#FFFFFF' },
    text: { primary: '#1A1A2E', secondary: '#5A6A7E' },
  },
  typography: {
    fontFamily: '"Inter", system-ui, -apple-system, sans-serif',
    h1: { fontWeight: 700, fontSize: '2rem' },
    h2: { fontWeight: 700, fontSize: '1.5rem' },
    h3: { fontWeight: 600, fontSize: '1.25rem' },
    h4: { fontWeight: 600, fontSize: '1.1rem' },
    h5: { fontWeight: 600, fontSize: '1rem' },
    h6: { fontWeight: 600, fontSize: '0.9rem' },
    body1: { fontSize: '0.95rem' },
    body2: { fontSize: '0.85rem' },
    caption: { fontSize: '0.75rem', color: '#5A6A7E' },
  },
  shape: { borderRadius: 10 },
  shadows: [
    'none',
    '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
    '0 2px 8px rgba(0,0,0,0.08)',
    '0 4px 16px rgba(0,0,0,0.10)',
    '0 8px 24px rgba(0,0,0,0.12)',
    ...Array(20).fill('0 8px 24px rgba(0,0,0,0.12)'),
  ],
  components: {
    MuiButton: {
      styleOverrides: {
        root: { textTransform: 'none', fontWeight: 600, borderRadius: 8 },
        containedPrimary: {
          background: 'linear-gradient(135deg, #1565C0 0%, #1E88E5 100%)',
          '&:hover': { background: 'linear-gradient(135deg, #0D47A1 0%, #1565C0 100%)' },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
          border: '1px solid rgba(0,0,0,0.06)',
        },
      },
    },
    MuiChip: {
      styleOverrides: { root: { fontWeight: 600, fontSize: '0.78rem' } },
    },
    MuiPaper: {
      styleOverrides: {
        root: { backgroundImage: 'none' },
      },
    },
  },
})

export default theme
