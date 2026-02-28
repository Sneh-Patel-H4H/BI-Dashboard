import { Paper, Typography, Box } from '@mui/material'
import Plot from 'react-plotly.js'

export default function ChartPanel({ title, plotlyJson }) {
  if (!plotlyJson) return null

  let data, layout, config
  try {
    const parsed = typeof plotlyJson === 'string' ? JSON.parse(plotlyJson) : plotlyJson
    data = parsed.data || []
    layout = {
      ...parsed.layout,
      autosize: true,
      margin: { l: 48, r: 24, t: 48, b: 48 },
      plot_bgcolor: '#FFFFFF',
      paper_bgcolor: '#FFFFFF',
      font: { family: 'Inter, system-ui, sans-serif', color: '#1A1A2E' },
    }
    config = { responsive: true, displayModeBar: false }
  } catch {
    return null
  }

  return (
    <Paper sx={{ p: 2.5, height: '100%' }}>
      <Typography variant="h6" sx={{ mb: 1.5, fontWeight: 600, color: 'text.primary', fontSize: '0.95rem' }}>
        {title}
      </Typography>
      <Box sx={{ width: '100%' }}>
        <Plot
          data={data}
          layout={layout}
          config={config}
          style={{ width: '100%', height: 280 }}
          useResizeHandler
        />
      </Box>
    </Paper>
  )
}
