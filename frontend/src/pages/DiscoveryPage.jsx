import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box, Typography, Paper, Grid, Button, Chip, Stack,
  Checkbox, FormControlLabel, Divider, Alert,
} from '@mui/material'
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch'
import { useData } from '../context/DataContext'
import SectorBadge from '../components/SectorBadge'
import ConfidenceBadge from '../components/ConfidenceBadge'

export default function DiscoveryPage() {
  const navigate = useNavigate()
  const { state, update } = useData()
  const { schema, totalRows, columnCount, dateRange, qualityNotes } = state

  const [selectedKpis, setSelectedKpis] = useState(
    (schema?.suggested_kpis || []).filter(k => k.priority === 'high')
  )

  const toggleKpi = (kpi) => {
    setSelectedKpis(prev =>
      prev.find(k => k.name === kpi.name)
        ? prev.filter(k => k.name !== kpi.name)
        : [...prev, kpi]
    )
  }

  const buildDashboard = () => {
    update({ selectedKpis, discoveryComplete: true })
    navigate('/dashboard')
  }

  if (!schema) return null

  const highKpis = (schema.suggested_kpis || []).filter(k => k.priority === 'high')
  const otherKpis = (schema.suggested_kpis || []).filter(k => k.priority !== 'high')

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', p: { xs: 2, md: 4 } }}>
      <Box sx={{ maxWidth: 900, mx: 'auto' }}>

        {/* Animated header */}
        <Box textAlign="center" mb={4}>
          <Typography fontSize={52} lineHeight={1} mb={1} sx={{ animation: 'pop 0.5s ease' }}>✨</Typography>
          <Typography variant="h2" gutterBottom>Here is what I found in your data</Typography>
          <Typography variant="body1" color="text.secondary">
            Review the AI analysis below, then build your dashboard.
          </Typography>
        </Box>

        {/* Sector + Org row */}
        <Grid container spacing={3} mb={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="overline" color="text.secondary" fontWeight={600}>Detected Sector</Typography>
              <Box mt={1} mb={1.5}>
                <SectorBadge sector={schema.sector} />
                <ConfidenceBadge level={schema.sector_confidence} sx={{ ml: 1 }} />
              </Box>
              <Typography variant="body2" color="text.secondary">{schema.sector_reasoning}</Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3, height: '100%' }}>
              <Typography variant="overline" color="text.secondary" fontWeight={600}>Organisation Type</Typography>
              <Box mt={1} mb={1.5}>
                <Chip label={schema.organization_type} sx={{ bgcolor: '#1A1A2E', color: '#fff', fontWeight: 600, fontSize: '0.85rem' }} />
                <ConfidenceBadge level={schema.org_confidence} sx={{ ml: 1 }} />
              </Box>
              <Typography variant="body2" color="text.secondary">{schema.org_reasoning}</Typography>
            </Paper>
          </Grid>
        </Grid>

        {/* Dataset summary */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h5" gutterBottom>Dataset Summary</Typography>
          <Grid container spacing={3} mb={2}>
            <Grid item xs={6} sm={3}>
              <Typography variant="h3" color="primary.main">{totalRows.toLocaleString()}</Typography>
              <Typography variant="caption">Rows</Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="h3" color="primary.main">{columnCount}</Typography>
              <Typography variant="caption">Columns</Typography>
            </Grid>
            {dateRange && (
              <Grid item xs={12} sm={6}>
                <Typography variant="h6" color="primary.main">{dateRange}</Typography>
                <Typography variant="caption">Date Range</Typography>
              </Grid>
            )}
          </Grid>
          {schema.dataset_description && (
            <Typography variant="body2" color="text.secondary" fontStyle="italic">
              {schema.dataset_description}
            </Typography>
          )}
        </Paper>

        {/* Data quality warnings */}
        {qualityNotes.length > 0 && (
          <Box mb={3}>
            {qualityNotes.map((note, i) => (
              <Alert key={i} severity="warning" sx={{ mb: 1 }}>{note}</Alert>
            ))}
          </Box>
        )}

        {/* KPI selection */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h5" gutterBottom>Proposed KPIs</Typography>
          <Typography variant="body2" color="text.secondary" mb={2}>
            Uncheck any KPIs you don't want to see on your dashboard.
          </Typography>

          <Stack spacing={1}>
            {highKpis.map(kpi => (
              <FormControlLabel
                key={kpi.name}
                control={
                  <Checkbox
                    checked={!!selectedKpis.find(k => k.name === kpi.name)}
                    onChange={() => toggleKpi(kpi)}
                    color="primary"
                  />
                }
                label={
                  <Box>
                    <Typography variant="body1" fontWeight={600} component="span">{kpi.name}</Typography>
                    <Typography variant="body2" color="text.secondary" component="span" ml={1}>— {kpi.formula}</Typography>
                  </Box>
                }
              />
            ))}
          </Stack>

          {otherKpis.length > 0 && (
            <>
              <Divider sx={{ my: 2 }} />
              <Typography variant="caption" color="text.secondary" mb={1} display="block">Additional metrics (optional)</Typography>
              <Stack spacing={1}>
                {otherKpis.map(kpi => (
                  <FormControlLabel
                    key={kpi.name}
                    control={
                      <Checkbox
                        checked={!!selectedKpis.find(k => k.name === kpi.name)}
                        onChange={() => toggleKpi(kpi)}
                        color="primary"
                        size="small"
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="body2" fontWeight={500} component="span">{kpi.name}</Typography>
                        <Typography variant="caption" color="text.secondary" component="span" ml={1}>— {kpi.formula}</Typography>
                      </Box>
                    }
                  />
                ))}
              </Stack>
            </>
          )}
        </Paper>

        {/* CTA */}
        <Box textAlign="center">
          <Button
            variant="contained"
            size="large"
            disabled={selectedKpis.length === 0}
            onClick={buildDashboard}
            startIcon={<RocketLaunchIcon />}
            sx={{ px: 6, py: 1.75, fontSize: '1rem' }}
          >
            Build My Dashboard
          </Button>
          {selectedKpis.length === 0 && (
            <Typography variant="caption" display="block" mt={1} color="text.secondary">
              Select at least one KPI to continue
            </Typography>
          )}
        </Box>
      </Box>

      <style>{`@keyframes pop { 0%{transform:scale(0.5);opacity:0} 70%{transform:scale(1.1)} 100%{transform:scale(1);opacity:1} }`}</style>
    </Box>
  )
}
