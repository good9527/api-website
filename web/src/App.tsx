import { Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './components/common/ThemeProvider'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Monitor from './pages/Monitor'
import ApiDocs from './pages/ApiDocs'
import History from './pages/History'
import Download from './pages/Download'
import Admin from './pages/Admin'
import ApiTest from './pages/ApiTest'

function App() {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="api-platform-theme">
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/monitor" element={<Monitor />} />
          <Route path="/api-docs" element={<ApiDocs />} />
          <Route path="/history" element={<History />} />
          <Route path="/download" element={<Download />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/api-test" element={<ApiTest />} />
        </Routes>
      </Layout>
    </ThemeProvider>
  )
}

export default App