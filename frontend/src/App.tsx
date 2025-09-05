import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { AuditLogs } from './pages/AuditLogs'
import { CreateEvent } from './pages/CreateEvent'
import { EventDetails } from './pages/EventDetails'
import MCPQuery from './pages/MCPQuery'
import { Settings } from './pages/Settings'
import { AlertManagement } from './pages/AlertManagement'
import { EventFramework } from './pages/EventFramework'
import EventPipelineBuilder from './pages/EventPipelineBuilder'
import { Alerts } from './pages/Alerts'
import { OutageMonitoring } from './pages/OutageMonitoring'
import ProductStatus from './pages/ProductStatus'
import { FeatureFlagsProvider, useFeatureFlags } from './contexts/FeatureFlagsContext'
import { AppSettingsProvider } from './contexts/AppSettingsContext'

function AppRoutes() {
  const { isFeatureEnabled } = useFeatureFlags();

  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/audit-logs" element={<AuditLogs />} />
      <Route path="/create-event" element={<CreateEvent />} />
      <Route path="/events/:id" element={<EventDetails />} />
      <Route path="/mcp-query" element={<MCPQuery />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="/alert-management" element={<AlertManagement />} />
      {isFeatureEnabled('eventFramework') && (
        <Route path="/event-framework" element={<EventFramework />} />
      )}
      {isFeatureEnabled('eventPipeline') && (
        <Route path="/event-pipeline-builder" element={<EventPipelineBuilder />} />
      )}
      <Route path="/alerts" element={<Alerts />} />
      <Route path="/outage-monitoring" element={<OutageMonitoring />} />
      <Route path="/product-status" element={<ProductStatus />} />
    </Routes>
  );
}

function App() {
  return (
    <AppSettingsProvider>
      <FeatureFlagsProvider>
        <Layout>
          <AppRoutes />
        </Layout>
      </FeatureFlagsProvider>
    </AppSettingsProvider>
  )
}

export default App
