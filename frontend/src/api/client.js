import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

/** Upload a file and receive full analysis in one shot. */
export async function uploadFile(file, sheet = null) {
  const form = new FormData()
  form.append('file', file)
  if (sheet) form.append('sheet', sheet)
  const { data } = await api.post('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120_000, // 2 min — analysis takes time
  })
  return data
}

/** Get sheet names from an Excel file (before full analysis). */
export async function getSheets(file) {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/sheets', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data.sheets
}

/** Send a chat question and receive a structured response. */
export async function sendChat({ question, schema, sampleRows, chatHistory }) {
  const { data } = await api.post('/chat', {
    question,
    schema,
    sample_rows: sampleRows,
    chat_history: chatHistory,
  })
  return data
}
