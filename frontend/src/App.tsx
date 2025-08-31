import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { AuditLogs } from './pages/AuditLogs'
import { CreateEvent } from './pages/CreateEvent'
import { EventDetails } from './pages/EventDetails'
import MCPQuery from './pages/MCPQuery'
import LLMProviders from './pages/LLMProviders'
import { CloudProjects } from './pages/CloudProjects'
import { EventSubscriptions } from './pages/EventSubscriptions'
import { CloudEvents } from './pages/CloudEvents'
import { AlertPolicies } from './pages/AlertPolicies'
import { AlertProviders } from './pages/AlertProviders'
import { Alerts } from './pages/Alerts'
import { AlertRules } from './pages/AlertRules'

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
        <Route path="/cloud-projects" element={<CloudProjects />} />
        <Route path="/event-subscriptions" element={<EventSubscriptions />} />
        <Route path="/cloud-events" element={<CloudEvents />} />
        <Route path="/alert-policies" element={<AlertPolicies />} />
        <Route path="/alert-providers" element={<AlertProviders />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/alert-rules" element={<AlertRules />} />
      </Routes>
    </Layout>
  )
}

export default App
