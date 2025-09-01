import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { AuditLogs } from './pages/AuditLogs'
import { CreateEvent } from './pages/CreateEvent'
import { EventDetails } from './pages/EventDetails'
import MCPQuery from './pages/MCPQuery'
import { Settings } from './pages/Settings'
import { AlertManagement } from './pages/AlertManagement'
import { EventSubscriptions } from './pages/EventSubscriptions'
import { CloudEvents } from './pages/CloudEvents'
import { Alerts } from './pages/Alerts'
import { OutageMonitoring } from './pages/OutageMonitoring'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/audit-logs" element={<AuditLogs />} />
        <Route path="/create-event" element={<CreateEvent />} />
        <Route path="/events/:id" element={<EventDetails />} />
        <Route path="/mcp-query" element={<MCPQuery />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/alert-management" element={<AlertManagement />} />
        <Route path="/event-subscriptions" element={<EventSubscriptions />} />
        <Route path="/cloud-events" element={<CloudEvents />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/outage-monitoring" element={<OutageMonitoring />} />
      </Routes>
    </Layout>
  )
}

export default App
