import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box, Grid, Typography, Button, Stack, Chip, Drawer,
  IconButton, Tooltip, AppBar, Toolbar,
} from '@mui/material'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import ChatIcon from '@mui/icons-material/Chat'
import UploadIcon from '@mui/icons-material/Upload'
import CloseIcon from '@mui/icons-material/Close'
import { useData } from '../context/DataContext'
import KPICard from '../components/KPICard'
import ChartPanel from '../components/ChartPanel'
import ChatPanel from '../components/ChatPanel'
import SectorBadge from '../components/SectorBadge'

const CHAT_WIDTH = 400

export default function DashboardPage() {
  const navigate = useNavigate()
  const { state, reset } = useData()
  const { schema, kpis, charts, selectedKpis, fileName } = state
  const [chatOpen, setChatOpen] = useState(false)

  const handleNewFile = () => {
    reset()
    navigate('/')
  }

  const kpiEntries = Object.entries(kpis || {}).filter(([, v]) => v?.value !== null)

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden', bgcolor: 'background.default' }}>
      {/* Main content */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', transition: 'margin 0.3s', mr: chatOpen ? `${CHAT_WIDTH}px` : 0 }}>

        {/* Top bar */}
        <AppBar position="static" elevation={0} sx={{ bgcolor: '#fff', borderBottom: '1px solid rgba(0,0,0,0.08)', color: 'text.primary' }}>
          <Toolbar sx={{ gap: 2 }}>
            <AutoAwesomeIcon color="primary" />
            <Typography variant="h6" fontWeight={700} sx={{ flex: 1 }}>Your Dashboard</Typography>

            {schema?.sector && <SectorBadge sector={schema.sector} />}
            {fileName && <Chip label={fileName} variant="outlined" size="small" sx={{ maxWidth: 160, fontSize: '0.75rem' }} />}

            <Tooltip title="Upload new file">
              <Button startIcon={<UploadIcon />} size="small" onClick={handleNewFile} variant="outlined">
                New File
              </Button>
            </Tooltip>
            <Tooltip title={chatOpen ? 'Close chat' : 'Ask your data'}>
              <Button
                startIcon={chatOpen ? <CloseIcon /> : <ChatIcon />}
                variant={chatOpen ? 'outlined' : 'contained'}
                size="small"
                onClick={() => setChatOpen(v => !v)}
              >
                {chatOpen ? 'Close Chat' : 'Ask the Data'}
              </Button>
            </Tooltip>
          </Toolbar>
        </AppBar>

        {/* Scrollable content */}
        <Box sx={{ flex: 1, overflowY: 'auto', p: 3 }}>

          {/* KPI cards */}
          {kpiEntries.length > 0 && (
            <>
              <Typography variant="overline" color="text.secondary" fontWeight={700} mb={2} display="block">
                Key Metrics
              </Typography>
              <Grid container spacing={2} mb={4}>
                {kpiEntries.map(([name, data]) => (
                  <Grid item xs={12} sm={6} md={3} key={name}>
                    <KPICard
                      name={name}
                      formattedValue={data.formatted_value}
                      changePct={data.change_pct}
                      changeDirection={data.change_direction}
                    />
                  </Grid>
                ))}
              </Grid>
            </>
          )}

          {/* Charts */}
          {charts.length > 0 && (
            <>
              <Typography variant="overline" color="text.secondary" fontWeight={700} mb={2} display="block">
                Charts
              </Typography>
              <Grid container spacing={3}>
                {charts.map((chart, i) => (
                  <Grid item xs={12} md={charts.length === 1 ? 12 : 6} key={i}>
                    <ChartPanel title={chart.title} plotlyJson={chart.plotly_json} />
                  </Grid>
                ))}
              </Grid>
            </>
          )}

          {kpiEntries.length === 0 && charts.length === 0 && (
            <Box textAlign="center" mt={8}>
              <Typography variant="h5" color="text.secondary">No visualisations available for this dataset.</Typography>
              <Typography variant="body2" color="text.secondary" mt={1}>Try asking a question in the chat panel.</Typography>
            </Box>
          )}

          {/* Footer */}
          <Box mt={6} textAlign="center">
            <Typography variant="caption" color="text.disabled">✨ Powered by Claude AI</Typography>
          </Box>
        </Box>
      </Box>

      {/* Chat drawer */}
      <Drawer
        anchor="right"
        open={chatOpen}
        variant="persistent"
        sx={{
          width: CHAT_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': { width: CHAT_WIDTH, boxSizing: 'border-box', border: 'none' },
        }}
      >
        <ChatPanel />
      </Drawer>
    </Box>
  )
}
