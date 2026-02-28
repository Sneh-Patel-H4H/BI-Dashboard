import { useState, useRef, useEffect } from 'react'
import {
  Box, Paper, Typography, TextField, IconButton, Stack,
  CircularProgress, Divider, Chip, Table, TableHead,
  TableBody, TableRow, TableCell, TableContainer, Alert,
} from '@mui/material'
import SendIcon from '@mui/icons-material/Send'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import Plot from 'react-plotly.js'
import { useData } from '../context/DataContext'
import { sendChat } from '../api/client'

export default function ChatPanel() {
  const { state, update } = useData()
  const { schema, sampleRows, chatHistory, isChatLoading } = state
  const [input, setInput] = useState('')
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatHistory, isChatLoading])

  const submit = async (question) => {
    const q = (question || input).trim()
    if (!q || isChatLoading) return
    setInput('')

    const userMsg = { role: 'user', content: q }
    const newHistory = [...chatHistory, userMsg]
    update({ chatHistory: newHistory, isChatLoading: true })

    try {
      const res = await sendChat({ question: q, schema, sampleRows, chatHistory: newHistory })
      const aiMsg = {
        role: 'assistant',
        content: res.insight_text,
        responseType: res.response_type,
        plotlyJson: res.plotly_json,
        tableRows: res.table_rows,
        tableColumns: res.table_columns,
        followUps: res.follow_up_suggestions || [],
      }
      update({ chatHistory: [...newHistory, aiMsg], isChatLoading: false })
    } catch (err) {
      const errMsg = {
        role: 'assistant',
        content: err?.response?.data?.detail || 'Something went wrong. Please try again.',
        responseType: 'narrative',
        followUps: [],
      }
      update({ chatHistory: [...newHistory, errMsg], isChatLoading: false })
    }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', bgcolor: 'background.paper', borderLeft: '1px solid rgba(0,0,0,0.08)' }}>
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: '1px solid rgba(0,0,0,0.08)', background: 'linear-gradient(135deg, #0A2342 0%, #1565C0 100%)' }}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <AutoAwesomeIcon sx={{ color: '#fff', fontSize: 20 }} />
          <Typography variant="h6" sx={{ color: '#fff', fontSize: '0.95rem', fontWeight: 600 }}>
            Ask Your Data
          </Typography>
        </Stack>
        <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)' }}>
          Ask anything in plain English
        </Typography>
      </Box>

      {/* Messages */}
      <Box sx={{ flex: 1, overflowY: 'auto', p: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
        {chatHistory.length === 0 && (
          <Box textAlign="center" mt={4}>
            <AutoAwesomeIcon sx={{ fontSize: 40, color: 'primary.light', mb: 1 }} />
            <Typography variant="body2" color="text.secondary" mb={2}>
              Ask me anything about your data
            </Typography>
            <Stack spacing={1}>
              {['What is the total revenue?', 'Show me the top performing categories', 'What trends do you see in the data?'].map(s => (
                <Chip key={s} label={s} variant="outlined" size="small" onClick={() => submit(s)}
                  sx={{ cursor: 'pointer', justifyContent: 'flex-start', '&:hover': { bgcolor: 'primary.main', color: '#fff' } }} />
              ))}
            </Stack>
          </Box>
        )}

        {chatHistory.map((msg, i) => (
          <MessageBubble key={i} msg={msg} onFollowUp={submit} />
        ))}

        {isChatLoading && (
          <Box display="flex" alignItems="center" gap={1} pl={1}>
            <CircularProgress size={16} />
            <Typography variant="caption" color="text.secondary">Thinking…</Typography>
          </Box>
        )}
        <div ref={bottomRef} />
      </Box>

      {/* Input */}
      <Divider />
      <Box sx={{ p: 1.5, display: 'flex', gap: 1 }}>
        <TextField
          fullWidth size="small" placeholder="Ask a question…" value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), submit())}
          disabled={isChatLoading}
          sx={{ '& .MuiOutlinedInput-root': { borderRadius: 3 } }}
        />
        <IconButton color="primary" disabled={!input.trim() || isChatLoading} onClick={() => submit()}
          sx={{ bgcolor: 'primary.main', color: '#fff', '&:hover': { bgcolor: 'primary.dark' }, '&:disabled': { bgcolor: 'action.disabledBackground' } }}>
          <SendIcon fontSize="small" />
        </IconButton>
      </Box>
    </Box>
  )
}

function MessageBubble({ msg, onFollowUp }) {
  const isUser = msg.role === 'user'
  return (
    <Box sx={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
      <Box sx={{ maxWidth: '92%', width: isUser ? 'auto' : '100%' }}>
        <Paper
          elevation={0}
          sx={{
            px: 2, py: 1.5, borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
            bgcolor: isUser ? 'primary.main' : 'grey.50',
            color: isUser ? '#fff' : 'text.primary',
            border: isUser ? 'none' : '1px solid rgba(0,0,0,0.07)',
          }}
        >
          {msg.content && (
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
              {msg.content}
            </Typography>
          )}
        </Paper>

        {/* Chart */}
        {msg.plotlyJson && <ChatChart plotlyJson={msg.plotlyJson} />}

        {/* Table */}
        {msg.tableRows && msg.tableColumns && <ChatTable rows={msg.tableRows} columns={msg.tableColumns} />}

        {/* Response type label */}
        {!isUser && msg.responseType && msg.responseType !== 'narrative' && (
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            {msg.responseType === 'chart' ? 'Chart' : msg.responseType === 'table' ? 'Table' : 'Chart + Insight'}
          </Typography>
        )}

        {/* Follow-up suggestions */}
        {!isUser && msg.followUps?.length > 0 && (
          <Stack direction="row" flexWrap="wrap" gap={0.5} mt={1}>
            {msg.followUps.map((s, i) => (
              <Chip key={i} label={s} size="small" variant="outlined" onClick={() => onFollowUp(s)}
                sx={{ cursor: 'pointer', fontSize: '0.72rem', '&:hover': { bgcolor: 'primary.main', color: '#fff' } }} />
            ))}
          </Stack>
        )}
      </Box>
    </Box>
  )
}

function ChatChart({ plotlyJson }) {
  try {
    const parsed = typeof plotlyJson === 'string' ? JSON.parse(plotlyJson) : plotlyJson
    return (
      <Box mt={1} sx={{ borderRadius: 2, overflow: 'hidden', border: '1px solid rgba(0,0,0,0.07)' }}>
        <Plot
          data={parsed.data || []}
          layout={{ ...parsed.layout, autosize: true, margin: { l: 40, r: 16, t: 32, b: 40 }, plot_bgcolor: '#FFFFFF', paper_bgcolor: '#FFFFFF', font: { size: 11 } }}
          config={{ responsive: true, displayModeBar: false }}
          style={{ width: '100%', height: 220 }}
          useResizeHandler
        />
      </Box>
    )
  } catch { return null }
}

function ChatTable({ rows, columns }) {
  return (
    <TableContainer component={Paper} variant="outlined" sx={{ mt: 1, maxHeight: 220 }}>
      <Table size="small" stickyHeader>
        <TableHead>
          <TableRow>
            {columns.map(c => <TableCell key={c} sx={{ fontWeight: 600, fontSize: '0.75rem', bgcolor: 'grey.50' }}>{c}</TableCell>)}
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.slice(0, 20).map((row, i) => (
            <TableRow key={i} hover>
              {columns.map(c => <TableCell key={c} sx={{ fontSize: '0.75rem' }}>{String(row[c] ?? '')}</TableCell>)}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  )
}
