import { createContext, useContext, useState } from 'react'

const DataContext = createContext(null)

export function DataProvider({ children }) {
  const [state, setState] = useState({
    // Upload flow
    uploadComplete: false,
    discoveryComplete: false,
    fileName: null,

    // Full analysis from /api/upload
    schema: null,
    kpis: null,
    charts: [],
    sampleRows: [],
    totalRows: 0,
    columnCount: 0,
    qualityNotes: [],
    dateRange: '',

    // User selections on discovery page
    selectedKpis: [],

    // Chat
    chatHistory: [],
    isChatLoading: false,
  })

  const update = (patch) => setState((prev) => ({ ...prev, ...patch }))

  const reset = () =>
    setState({
      uploadComplete: false,
      discoveryComplete: false,
      fileName: null,
      schema: null,
      kpis: null,
      charts: [],
      sampleRows: [],
      totalRows: 0,
      columnCount: 0,
      qualityNotes: [],
      dateRange: '',
      selectedKpis: [],
      chatHistory: [],
      isChatLoading: false,
    })

  return (
    <DataContext.Provider value={{ state, update, reset }}>
      {children}
    </DataContext.Provider>
  )
}

export function useData() {
  const ctx = useContext(DataContext)
  if (!ctx) throw new Error('useData must be used inside DataProvider')
  return ctx
}
