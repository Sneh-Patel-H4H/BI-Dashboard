import { Chip } from '@mui/material'

const COLORS = { High: '#27AE60', Medium: '#F39C12', Low: '#E74C3C' }

export default function ConfidenceBadge({ level, sx }) {
  const color = COLORS[level] || '#95A5A6'
  return (
    <Chip
      label={`${level || '?'} Confidence`}
      size="small"
      sx={{ bgcolor: color, color: '#fff', fontWeight: 600, fontSize: '0.72rem', ...sx }}
    />
  )
}
