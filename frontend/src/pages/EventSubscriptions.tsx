import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, TestTube, Bell } from 'lucide-react'
import { eventsApi, EventSubscription, CloudProject } from '@/lib/api'

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
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
  { value: 'info', label: 'Info' },
]

export function EventSubscriptions() {
  const [subscriptions, setSubscriptions] = useState<EventSubscription[]>([])
  const [projects, setProjects] = useState<CloudProject[]>([])
  const [loading, setLoading] = useState(true)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [selectedSubscription, setSelectedSubscription] = useState<EventSubscription | null>(null)
  const [testingSubscription, setTestingSubscription] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    project_id: '',
    event_types: [] as string[],
    severity_levels: [] as string[],
    services: [] as string[],
    regions: [] as string[],
    enabled: true,
    webhook_url: '',
    webhook_headers: '',
    filters: '',
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [subscriptionsResponse, projectsResponse] = await Promise.all([
        eventsApi.getEventSubscriptions(),
        eventsApi.getCloudProjects()
      ])
      setSubscriptions(subscriptionsResponse.items || [])
      setProjects(projectsResponse.items || [])
    } catch (error) {
      console.error('Failed to load data:', error)
      showToast('Failed to load event subscriptions', 'error')
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      project_id: '',
      event_types: [],
      severity_levels: [],
      services: [],
      regions: [],
      enabled: true,
      webhook_url: '',
      webhook_headers: '',
      filters: '',
    })
  }

  const handleCreate = () => {
    resetForm()
    setIsCreateDialogOpen(true)
  }

  const handleEdit = (subscription: EventSubscription) => {
    setFormData({
      name: subscription.name,
      description: subscription.description || '',
      project_id: subscription.project_id,
      event_types: subscription.event_types || [],
      severity_levels: subscription.severity_levels || [],
      services: subscription.services || [],
      regions: subscription.regions || [],
      enabled: subscription.enabled,
      webhook_url: subscription.webhook_url || '',
      webhook_headers: subscription.webhook_headers ? JSON.stringify(subscription.webhook_headers, null, 2) : '',
      filters: subscription.filters ? JSON.stringify(subscription.filters, null, 2) : '',
    })
    setSelectedSubscription(subscription)
    setIsEditDialogOpen(true)
  }

  const handleDelete = async (subscriptionId: string) => {
    if (!confirm('Are you sure you want to delete this subscription?')) return

    try {
      await eventsApi.deleteEventSubscription(subscriptionId)
      showToast('Subscription deleted successfully')
      loadData()
    } catch (error) {
      console.error('Failed to delete subscription:', error)
      showToast('Failed to delete subscription', 'error')
    }
  }

  const handleTestSubscription = async (subscriptionId: string) => {
    try {
      setTestingSubscription(subscriptionId)
      await eventsApi.testEventSubscription(subscriptionId)
      showToast('Test event sent successfully')
    } catch (error) {
      console.error('Failed to test subscription:', error)
      showToast('Failed to test subscription', 'error')
    } finally {
      setTestingSubscription(null)
    }
  }

  const handleSubmit = async () => {
    try {
      const subscriptionData = {
        ...formData,
        webhook_headers: formData.webhook_headers ? JSON.parse(formData.webhook_headers) : {},
        filters: formData.filters ? JSON.parse(formData.filters) : {},
      }

      if (isEditDialogOpen && selectedSubscription) {
        await eventsApi.updateEventSubscription(selectedSubscription.subscription_id, subscriptionData)
        showToast('Subscription updated successfully')
      } else {
        await eventsApi.createEventSubscription(subscriptionData)
        showToast('Subscription created successfully')
      }

      setIsCreateDialogOpen(false)
      setIsEditDialogOpen(false)
      setSelectedSubscription(null)
      resetForm()
      loadData()
    } catch (error) {
      console.error('Failed to save subscription:', error)
      showToast('Failed to save subscription', 'error')
    }
  }

  const getProjectName = (projectId: string) => {
    const project = projects.find(p => p.project_id === projectId)
    return project ? `${project.name} (${project.cloud_provider})` : 'Unknown Project'
  }

  const getStats = (subscription: EventSubscription) => {
    return {
      total_events: subscription.stats?.total_events || 0,
      events_last_24h: subscription.stats?.events_last_24h || 0,
      events_last_7d: subscription.stats?.events_last_7d || 0,
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading event subscriptions...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Event Subscriptions</h1>
          <p className="text-gray-600 mt-2">
            Manage event subscriptions for cloud projects
          </p>
        </div>
        <button
          onClick={handleCreate}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Subscription
        </button>
      </div>

      {/* Subscriptions List */}
      <div className="grid gap-6">
        {subscriptions.length === 0 ? (
          <div className="card">
            <div className="p-6 text-center">
              <Bell className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No subscriptions found</h3>
              <p className="text-gray-600 mb-4">
                Create your first event subscription to start receiving cloud events
              </p>
              <button
                onClick={handleCreate}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                Create Subscription
              </button>
            </div>
          </div>
        ) : (
          subscriptions.map((subscription) => {
            const stats = getStats(subscription)
            return (
              <div key={subscription.subscription_id} className="card">
                <div className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-semibold">{subscription.name}</h3>
                      <p className="text-gray-600">{subscription.description}</p>
                    </div>
                    <div className="flex space-x-1">
                      <button
                        className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                        onClick={() => handleTestSubscription(subscription.subscription_id)}
                        disabled={testingSubscription === subscription.subscription_id}
                      >
                        <TestTube className="w-4 h-4" />
                      </button>
                      <button
                        className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                        onClick={() => handleEdit(subscription)}
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                        onClick={() => handleDelete(subscription.subscription_id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Project:</span>
                      <span className="text-sm font-medium">{getProjectName(subscription.project_id)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Status:</span>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        subscription.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {subscription.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Event Types:</span>
                      <span className="text-sm">
                        {subscription.event_types?.length ? 
                          subscription.event_types.map(type => 
                            EVENT_TYPES.find(t => t.value === type)?.label || type
                          ).join(', ') : 
                          'All types'
                        }
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Severity Levels:</span>
                      <span className="text-sm">
                        {subscription.severity_levels?.length ? 
                          subscription.severity_levels.map(level => 
                            SEVERITY_LEVELS.find(s => s.value === level)?.label || level
                          ).join(', ') : 
                          'All levels'
                        }
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Services:</span>
                      <span className="text-sm">
                        {subscription.services?.length ? subscription.services.join(', ') : 'All services'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Regions:</span>
                      <span className="text-sm">
                        {subscription.regions?.length ? subscription.regions.join(', ') : 'All regions'}
                      </span>
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t">
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <p className="text-sm text-gray-600">Total Events</p>
                        <p className="text-lg font-semibold">{stats.total_events}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Last 24h</p>
                        <p className="text-lg font-semibold">{stats.events_last_24h}</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Last 7d</p>
                        <p className="text-lg font-semibold">{stats.events_last_7d}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )
          })
        )}
      </div>

      {/* Create/Edit Dialog */}
      {(isCreateDialogOpen || isEditDialogOpen) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="mb-4">
              <h2 className="text-xl font-semibold">
                {isEditDialogOpen ? 'Edit Subscription' : 'Create Subscription'}
              </h2>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter subscription name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Enter description"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Project</label>
                <select
                  value={formData.project_id}
                  onChange={(e) => setFormData(prev => ({ ...prev, project_id: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select a project</option>
                  {projects.map(project => (
                    <option key={project.project_id} value={project.project_id}>
                      {project.name} ({project.cloud_provider})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Event Types</label>
                <div className="space-y-2">
                  {EVENT_TYPES.map(type => (
                    <label key={type.value} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formData.event_types.includes(type.value)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData(prev => ({ ...prev, event_types: [...prev.event_types, type.value] }))
                          } else {
                            setFormData(prev => ({ ...prev, event_types: prev.event_types.filter(t => t !== type.value) }))
                          }
                        }}
                        className="mr-2"
                      />
                      {type.label}
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Severity Levels</label>
                <div className="space-y-2">
                  {SEVERITY_LEVELS.map(level => (
                    <label key={level.value} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={formData.severity_levels.includes(level.value)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setFormData(prev => ({ ...prev, severity_levels: [...prev.severity_levels, level.value] }))
                          } else {
                            setFormData(prev => ({ ...prev, severity_levels: prev.severity_levels.filter(s => s !== level.value) }))
                          }
                        }}
                        className="mr-2"
                      />
                      {level.label}
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Webhook URL</label>
                <input
                  type="url"
                  value={formData.webhook_url}
                  onChange={(e) => setFormData(prev => ({ ...prev, webhook_url: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://your-webhook-url.com/events"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Webhook Headers (JSON)</label>
                <textarea
                  value={formData.webhook_headers}
                  onChange={(e) => setFormData(prev => ({ ...prev, webhook_headers: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder='{"Authorization": "Bearer token"}'
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Enabled</label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.enabled}
                    onChange={(e) => setFormData(prev => ({ ...prev, enabled: e.target.checked }))}
                    className="mr-2"
                  />
                  Enable this subscription
                </label>
              </div>
            </div>
            <div className="flex justify-end space-x-2 mt-6">
              <button
                onClick={() => {
                  setIsCreateDialogOpen(false)
                  setIsEditDialogOpen(false)
                  setSelectedSubscription(null)
                  resetForm()
                }}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmit}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                {isEditDialogOpen ? 'Update' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
