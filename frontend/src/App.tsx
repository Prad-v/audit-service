import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { AuditLogs } from './pages/AuditLogs'
import { CreateEvent } from './pages/CreateEvent'
import { EventDetails } from './pages/EventDetails'
import MCPQuery from './pages/MCPQuery'
import LLMProviders from './pages/LLMProviders'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/audit-logs" element={<AuditLogs />} />
        <Route path="/create-event" element={<CreateEvent />} />
        <Route path="/events/:id" element={<EventDetails />} />
        <Route path="/mcp-query" element={<MCPQuery />} />
        <Route path="/llm-providers" element={<LLMProviders />} />
      </Routes>
    </Layout>
  )
}

export default App
