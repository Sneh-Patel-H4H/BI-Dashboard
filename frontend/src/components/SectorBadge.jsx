import { Chip } from '@mui/material'

const COLORS = {
  'Ecommerce':            '#FF6B35',
  'Marketing':            '#9B59B6',
  'Sales/CRM':            '#1565C0',
  'SaaS/Product':         '#27AE60',
  'Customer Support':     '#7F8C8D',
  'Finance':              '#7F8C8D',
  'HR / People':          '#7F8C8D',
  'Logistics / Operations': '#E67E22',
  'Healthcare':           '#1ABC9C',
  'Mixed':                '#95A5A6',
}

export default function SectorBadge({ sector, sx }) {
  const color = COLORS[sector] || '#7F8C8D'
  return (
    <Chip
      label={sector || 'Unknown'}
      sx={{ bgcolor: color, color: '#fff', fontWeight: 700, fontSize: '0.85rem', ...sx }}
    />
  )
}
