import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box, Typography, Paper, Button, LinearProgress,
  Alert, Chip, Stack, CircularProgress,
} from '@mui/material'
import UploadFileIcon from '@mui/icons-material/UploadFile'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import { useData } from '../context/DataContext'
import { uploadFile, getSheets } from '../api/client'
import SheetSelector from '../components/SheetSelector'

const STEPS = [
  'Reading your file…',
  'Profiling columns…',
  'Running AI analysis…',
  'Generating dashboard…',
]

export default function UploadPage() {
  const navigate = useNavigate()
  const { update, reset } = useData()

  const [dragging, setDragging] = useState(false)
  const [file, setFile] = useState(null)
  const [sheets, setSheets] = useState([])
  const [selectedSheet, setSelectedSheet] = useState(null)
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleFile = useCallback(async (f) => {
    setError(null)
    setFile(f)
    setSheets([])
    setSelectedSheet(null)
    const ext = f.name.split('.').pop().toLowerCase()
    if (ext === 'xlsx' || ext === 'xls') {
      try {
        const s = await getSheets(f)
        if (s.length > 1) setSheets(s)
        else setSelectedSheet(null)
      } catch {
        // ignore — will be caught on upload
      }
    }
  }, [])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }, [handleFile])

  const onInputChange = (e) => {
    const f = e.target.files[0]
    if (f) handleFile(f)
  }

  const analyse = async () => {
    if (!file) return
    setLoading(true)
    setError(null)

    // Simulate step progression while upload processes
    let s = 0
    const ticker = setInterval(() => {
      s = Math.min(s + 1, STEPS.length - 1)
      setStep(s)
    }, 8000)

    try {
      reset()
      const result = await uploadFile(file, selectedSheet)
      clearInterval(ticker)

      update({
        uploadComplete: true,
        fileName: result.file_name,
        schema: result.schema,
        kpis: result.kpis,
        charts: result.charts,
        sampleRows: result.sample_rows,
        totalRows: result.total_rows,
        columnCount: result.column_count,
        qualityNotes: result.quality_notes,
        dateRange: result.date_range,
        selectedKpis: (result.schema?.suggested_kpis || []).filter(k => k.priority === 'high'),
      })
      navigate('/discovery')
    } catch (err) {
      clearInterval(ticker)
      const msg = err?.response?.data?.detail || err.message || 'Upload failed. Please try again.'
      setError(msg)
    } finally {
      setLoading(false)
      setStep(0)
    }
  }

  return (
    <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 3, background: 'linear-gradient(135deg, #0A2342 0%, #1565C0 100%)' }}>
      {/* Header */}
      <Stack direction="row" alignItems="center" spacing={1.5} mb={4}>
        <AutoAwesomeIcon sx={{ color: '#fff', fontSize: 32 }} />
        <Typography variant="h2" sx={{ color: '#fff', fontWeight: 700 }}>
          BI Dashboard
        </Typography>
      </Stack>

      <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.75)', mb: 5, textAlign: 'center', maxWidth: 480 }}>
        Upload any business data file and get an AI-generated dashboard instantly — no setup, no configuration required.
      </Typography>

      {/* Drop zone */}
      <Paper
        elevation={3}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        sx={{
          width: '100%', maxWidth: 560, p: 5, textAlign: 'center', cursor: 'pointer',
          border: '2px dashed', borderColor: dragging ? 'primary.main' : 'rgba(0,0,0,0.12)',
          bgcolor: dragging ? 'rgba(21,101,192,0.04)' : 'background.paper',
          transition: 'all 0.2s',
          borderRadius: 3,
        }}
        onClick={() => !loading && document.getElementById('file-input').click()}
      >
        <input id="file-input" type="file" accept=".csv,.xlsx,.xls" hidden onChange={onInputChange} />

        {loading ? (
          <Box>
            <CircularProgress size={48} sx={{ mb: 2 }} />
            <Typography variant="h6" gutterBottom>{STEPS[step]}</Typography>
            <LinearProgress sx={{ mt: 1, borderRadius: 4 }} />
            <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
              This takes 20–40 seconds — AI is analysing your data
            </Typography>
          </Box>
        ) : (
          <>
            <UploadFileIcon sx={{ fontSize: 56, color: 'primary.main', mb: 2 }} />
            {file ? (
              <>
                <Chip label={file.name} color="primary" variant="outlined" sx={{ mb: 2 }} />
                <Typography variant="body2" color="text.secondary">
                  Click to change file
                </Typography>
              </>
            ) : (
              <>
                <Typography variant="h6" gutterBottom>Drop your file here</Typography>
                <Typography variant="body2" color="text.secondary">
                  Supports CSV and Excel (.xlsx) — headers can be anywhere in the first 10 rows
                </Typography>
              </>
            )}
          </>
        )}
      </Paper>

      {/* Sheet selector */}
      {sheets.length > 1 && !loading && (
        <SheetSelector
          sheets={sheets}
          selected={selectedSheet}
          onChange={setSelectedSheet}
          sx={{ mt: 2, maxWidth: 560, width: '100%' }}
        />
      )}

      {/* Error */}
      {error && (
        <Alert severity="error" sx={{ mt: 2, maxWidth: 560, width: '100%' }}>
          {error}
        </Alert>
      )}

      {/* Analyse button */}
      {file && !loading && (
        <Button
          variant="contained"
          size="large"
          disabled={sheets.length > 1 && !selectedSheet}
          onClick={analyse}
          sx={{ mt: 3, px: 6, py: 1.5, fontSize: '1rem' }}
          startIcon={<AutoAwesomeIcon />}
        >
          Analyse My Data
        </Button>
      )}

      {/* Capability chips */}
      {!file && !loading && (
        <Stack direction="row" spacing={1} flexWrap="wrap" justifyContent="center" mt={4}>
          {['Sector detection', 'Auto KPIs', 'Smart charts', 'Chat Q&A'].map(label => (
            <Chip key={label} label={label} size="small" sx={{ bgcolor: 'rgba(255,255,255,0.15)', color: '#fff', mb: 1 }} />
          ))}
        </Stack>
      )}
    </Box>
  )
}
