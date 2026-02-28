import { Paper, Typography, Box, Stack } from '@mui/material'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import TrendingDownIcon from '@mui/icons-material/TrendingDown'

export default function KPICard({ name, formattedValue, changePct, changeDirection }) {
  const hasChange = changePct !== null && changePct !== undefined
  const isUp = changeDirection === 'up'

  return (
    <Paper
      sx={{
        p: 3, height: '100%',
        background: 'linear-gradient(135deg, #fff 0%, #F8FAFF 100%)',
        border: '1px solid rgba(21,101,192,0.1)',
        transition: 'box-shadow 0.2s',
        '&:hover': { boxShadow: 3 },
      }}
    >
      <Typography variant="caption" color="text.secondary" fontWeight={600} textTransform="uppercase" letterSpacing={0.5}>
        {name}
      </Typography>
      <Typography variant="h3" sx={{ fontSize: { xs: '1.6rem', md: '2rem' }, fontWeight: 700, color: 'secondary.main', mt: 0.5, mb: 1 }}>
        {formattedValue}
      </Typography>
      {hasChange && (
        <Stack direction="row" alignItems="center" spacing={0.5}>
          {isUp
            ? <TrendingUpIcon sx={{ color: 'success.main', fontSize: 18 }} />
            : <TrendingDownIcon sx={{ color: 'error.main', fontSize: 18 }} />
          }
          <Typography variant="body2" fontWeight={600} color={isUp ? 'success.main' : 'error.main'}>
            {isUp ? '+' : ''}{changePct?.toFixed(1)}% vs prior period
          </Typography>
        </Stack>
      )}
    </Paper>
  )
}
