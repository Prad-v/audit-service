import { useState, useEffect } from 'react'
import { Eye, CheckCircle, XCircle, RefreshCw, AlertTriangle } from 'lucide-react'
import { eventsApi, cloudApi, CloudEvent, CloudProject, EventSubscription, EventsSummary } from '@/lib/api'

// Simple toast notification function
const showToast = (message: string, type: 'success' | 'error' = 'success') => {
  const toast = document.createElement('div')
  toast.className = `fixed top-4 right-4 px-4 py-2 rounded-md text-white z-50 ${
    type === 'success' ? 'bg-green-600' : 'bg-red-600'
  }`
  toast.textContent = message
  document.body.appendChild(toast)
  setTimeout(() => {
    document.body.removeChild(toast)
  }, 3000)
}

const EVENT_TYPES = [
  { value: 'grafana_alert', label: 'Grafana Alert' },
  { value: 'cloud_alert', label: 'Cloud Alert' },
  { value: 'outage_status', label: 'Outage Status' },
  { value: 'custom_event', label: 'Custom Event' },
]

const SEVERITY_LEVELS = [
  { value: 'critical', label: 'Critical', color: 'bg-red-100 text-red-800' },
  { value: 'high', label: 'High', color: 'bg-red-100 text-red-800' },
  { value: 'medium', label: 'Medium', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'low', label: 'Low', color: 'bg-blue-100 text-blue-800' },
  { value: 'info', label: 'Info', color: 'bg-gray-100 text-gray-800' },
]

const EVENT_STATUS = [
  { value: 'active', label: 'Active' },
  { value: 'acknowledged', label: 'Acknowledged' },
  { value: 'resolved', label: 'Resolved' },
]

export function CloudEvents() {
  const [events, setEvents] = useState<CloudEvent[]>([])
  const [projects, setProjects] = useState<CloudProject[]>([])
  const [subscriptions, setSubscriptions] = useState<EventSubscription[]>([])
  const [summary, setSummary] = useState<EventsSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedEvent, setSelectedEvent] = useState<CloudEvent | null>(null)
  const [isEventDialogOpen, setIsEventDialogOpen] = useState(false)

  const [filters] = useState({
    event_type: '',
    severity: '',
    status: '',
    cloud_provider: '',
    project_id: '',
    subscription_id: '',
    start_date: '',
    end_date: '',
    page: 1,
    per_page: 20,
  })

  useEffect(() => {
    loadData()
  }, [filters])

  const loadData = async () => {
    try {
      setLoading(true)
      const [eventsResponse, projectsResponse, subscriptionsResponse, summaryResponse] = await Promise.all([
        eventsApi.getCloudEvents(filters),
        cloudApi.getCloudProjects(),
        eventsApi.getEventSubscriptions(),
        eventsApi.getEventsSummary()
      ])
      setEvents(eventsResponse.items || [])
      setProjects(projectsResponse.items || [])
      setSubscriptions(subscriptionsResponse.items || [])
      setSummary(summaryResponse)
    } catch (error) {
      console.error('Failed to load data:', error)
      showToast('Failed to load cloud events', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    loadData()
  }

  const handleAcknowledgeEvent = async (eventId: string) => {
    try {
      await eventsApi.acknowledgeCloudEvent(eventId)
      showToast('Event acknowledged')
      loadData()
    } catch (error) {
      console.error('Failed to acknowledge event:', error)
      showToast('Failed to acknowledge event', 'error')
    }
  }

  const handleResolveEvent = async (eventId: string) => {
    try {
      await eventsApi.resolveCloudEvent(eventId)
      showToast('Event resolved')
      loadData()
    } catch (error) {
      console.error('Failed to resolve event:', error)
      showToast('Failed to resolve event', 'error')
    }
  }

  const openEventDialog = (event: CloudEvent) => {
    setSelectedEvent(event)
    setIsEventDialogOpen(true)
  }

  const getSeverityColor = (severity: string) => {
    const severityConfig = SEVERITY_LEVELS.find(s => s.value === severity)
    return severityConfig?.color || 'bg-gray-100 text-gray-800'
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-red-100 text-red-800'
      case 'acknowledged':
        return 'bg-yellow-100 text-yellow-800'
      case 'resolved':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString()
  }

  const getProjectName = (projectId?: string) => {
    if (!projectId) return 'N/A'
    const project = projects.find(p => p.project_id === projectId)
    return project ? `${project.name} (${project.cloud_provider})` : 'Unknown Project'
  }

  const getSubscriptionName = (subscriptionId?: string) => {
    if (!subscriptionId) return 'N/A'
    const subscription = subscriptions.find(s => s.subscription_id === subscriptionId)
    return subscription ? subscription.name : 'Unknown Subscription'
  }

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading cloud events...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Cloud Events</h1>
          <p className="text-gray-600 mt-2">
            Monitor and manage events from cloud providers
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 flex items-center"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <div className="card">
            <div className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Events</p>
                  <p className="text-2xl font-bold">{summary.total_events}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-gray-400" />
              </div>
            </div>
          </div>
          <div className="card">
            <div className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Last 24h</p>
                  <p className="text-2xl font-bold">{summary.events_last_24h}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-gray-400" />
              </div>
            </div>
          </div>
          <div className="card">
            <div className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Active Events</p>
                  <p className="text-2xl font-bold">{summary.active_events}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-gray-400" />
              </div>
            </div>
          </div>
          <div className="card">
            <div className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Last 7 Days</p>
                  <p className="text-2xl font-bold">{summary.events_last_7d}</p>
                </div>
                <AlertTriangle className="h-8 w-8 text-gray-400" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Events List */}
      <div className="card">
        <div className="p-6">
          <h2 className="text-lg font-semibold mb-4">Events ({events.length} found)</h2>
          {events.length === 0 ? (
            <div className="text-center py-8">
              <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No events found</h3>
              <p className="text-gray-600">
                No events match the current filters
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {events.map((event) => (
                <div key={event.event_id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <h3 className="font-semibold text-lg">{event.title}</h3>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(event.severity)}`}>
                          {SEVERITY_LEVELS.find(s => s.value === event.severity)?.label || event.severity}
                        </span>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(event.status)}`}>
                          {EVENT_STATUS.find(s => s.value === event.status)?.label || event.status}
                        </span>
                        <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                          {EVENT_TYPES.find(t => t.value === event.event_type)?.label || event.event_type}
                        </span>
                      </div>
                      <p className="text-gray-600 mb-2">{event.description}</p>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-500">
                        <div>
                          <span className="font-medium">Provider:</span> {event.cloud_provider}
                        </div>
                        <div>
                          <span className="font-medium">Project:</span> {getProjectName(event.project_id)}
                        </div>
                        <div>
                          <span className="font-medium">Service:</span> {event.service_name || 'N/A'}
                        </div>
                        <div>
                          <span className="font-medium">Region:</span> {event.region || 'N/A'}
                        </div>
                      </div>
                      <div className="text-sm text-gray-500 mt-2">
                        <span className="font-medium">Event Time:</span> {formatDate(event.event_time)}
                      </div>
                    </div>
                    <div className="flex space-x-2 ml-4">
                      <button
                        className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                        onClick={() => openEventDialog(event)}
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      {event.status === 'active' && (
                        <>
                          <button
                            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                            onClick={() => handleAcknowledgeEvent(event.event_id)}
                          >
                            <CheckCircle className="w-4 h-4" />
                          </button>
                          <button
                            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                            onClick={() => handleResolveEvent(event.event_id)}
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Event Details Dialog */}
      {isEventDialogOpen && selectedEvent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="mb-4">
              <h2 className="text-xl font-semibold">Event Details</h2>
              <p className="text-gray-600">
                Detailed information about the cloud event
              </p>
            </div>
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold mb-2">{selectedEvent.title}</h3>
                <p className="text-gray-600">{selectedEvent.description}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="font-medium">Event ID</label>
                  <p className="text-sm font-mono">{selectedEvent.event_id}</p>
                </div>
                <div>
                  <label className="font-medium">External ID</label>
                  <p className="text-sm">{selectedEvent.external_id || 'N/A'}</p>
                </div>
                <div>
                  <label className="font-medium">Event Type</label>
                  <p className="text-sm">{EVENT_TYPES.find(t => t.value === selectedEvent.event_type)?.label || selectedEvent.event_type}</p>
                </div>
                <div>
                  <label className="font-medium">Severity</label>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(selectedEvent.severity)}`}>
                    {SEVERITY_LEVELS.find(s => s.value === selectedEvent.severity)?.label || selectedEvent.severity}
                  </span>
                </div>
                <div>
                  <label className="font-medium">Status</label>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(selectedEvent.status)}`}>
                    {EVENT_STATUS.find(s => s.value === selectedEvent.status)?.label || selectedEvent.status}
                  </span>
                </div>
                <div>
                  <label className="font-medium">Cloud Provider</label>
                  <p className="text-sm">{selectedEvent.cloud_provider}</p>
                </div>
                <div>
                  <label className="font-medium">Project</label>
                  <p className="text-sm">{getProjectName(selectedEvent.project_id)}</p>
                </div>
                <div>
                  <label className="font-medium">Subscription</label>
                  <p className="text-sm">{getSubscriptionName(selectedEvent.subscription_id)}</p>
                </div>
                <div>
                  <label className="font-medium">Service Name</label>
                  <p className="text-sm">{selectedEvent.service_name || 'N/A'}</p>
                </div>
                <div>
                  <label className="font-medium">Resource Type</label>
                  <p className="text-sm">{selectedEvent.resource_type || 'N/A'}</p>
                </div>
                <div>
                  <label className="font-medium">Resource ID</label>
                  <p className="text-sm font-mono">{selectedEvent.resource_id || 'N/A'}</p>
                </div>
                <div>
                  <label className="font-medium">Region</label>
                  <p className="text-sm">{selectedEvent.region || 'N/A'}</p>
                </div>
              </div>

              <div>
                <label className="font-medium">Timestamps</label>
                <div className="grid grid-cols-2 gap-4 mt-2">
                  <div>
                    <span className="text-sm text-gray-500">Event Time:</span>
                    <p className="text-sm">{formatDate(selectedEvent.event_time)}</p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Created:</span>
                    <p className="text-sm">{formatDate(selectedEvent.created_at)}</p>
                  </div>
                  {selectedEvent.acknowledged_at && (
                    <div>
                      <span className="text-sm text-gray-500">Acknowledged:</span>
                      <p className="text-sm">{formatDate(selectedEvent.acknowledged_at)}</p>
                    </div>
                  )}
                  {selectedEvent.resolved_at && (
                    <div>
                      <span className="text-sm text-gray-500">Resolved:</span>
                      <p className="text-sm">{formatDate(selectedEvent.resolved_at)}</p>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <label className="font-medium">Summary</label>
                <p className="text-sm mt-1">{selectedEvent.summary}</p>
              </div>

              <div>
                <label className="font-medium">Raw Data</label>
                <pre className="text-xs bg-gray-100 p-4 rounded mt-1 overflow-auto max-h-40">
                  {JSON.stringify(selectedEvent.raw_data, null, 2)}
                </pre>
              </div>
            </div>
            <div className="flex justify-end mt-6">
              <button
                onClick={() => setIsEventDialogOpen(false)}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
