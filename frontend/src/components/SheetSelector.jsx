import { Paper, Typography, ToggleButtonGroup, ToggleButton } from '@mui/material'

export default function SheetSelector({ sheets, selected, onChange, sx }) {
  return (
    <Paper variant="outlined" sx={{ p: 2, borderRadius: 2, ...sx }}>
      <Typography variant="body2" fontWeight={600} mb={1}>
        This file has multiple sheets — select one to analyse:
      </Typography>
      <ToggleButtonGroup
        value={selected}
        exclusive
        onChange={(_, val) => val && onChange(val)}
        size="small"
        sx={{ flexWrap: 'wrap', gap: 0.5 }}
      >
        {sheets.map((s) => (
          <ToggleButton key={s} value={s} sx={{ borderRadius: '6px !important', textTransform: 'none', fontSize: '0.82rem' }}>
            {s}
          </ToggleButton>
        ))}
      </ToggleButtonGroup>
    </Paper>
  )
}
