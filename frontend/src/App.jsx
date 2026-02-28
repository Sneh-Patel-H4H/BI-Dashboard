import { Routes, Route, Navigate } from 'react-router-dom'
import { useData } from './context/DataContext'
import UploadPage from './pages/UploadPage'
import DiscoveryPage from './pages/DiscoveryPage'
import DashboardPage from './pages/DashboardPage'

export default function App() {
  const { state } = useData()

  return (
    <Routes>
      <Route path="/" element={<UploadPage />} />
      <Route
        path="/discovery"
        element={state.uploadComplete ? <DiscoveryPage /> : <Navigate to="/" replace />}
      />
      <Route
        path="/dashboard"
        element={state.discoveryComplete ? <DashboardPage /> : <Navigate to="/" replace />}
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
