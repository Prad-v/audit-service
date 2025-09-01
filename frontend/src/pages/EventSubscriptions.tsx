import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, TestTube, Bell, Webhook, Globe, MessageSquare, Database, AlertTriangle, Zap } from 'lucide-react'
import { eventsApi } from '@/lib/api'

// Define the new input source types
type InputSourceType = 'webhook' | 'http_client' | 'pubsub' | 'kinesis' | 'pagerduty' | 'nats'

interface InputSourceConfig {
  type: InputSourceType
  name: string
  description?: string
  enabled: boolean
  config: Record<string, any>
}

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

const INPUT_SOURCE_TYPES = [
  { 
    value: 'webhook', 
    label: 'Webhook Server', 
    icon: Webhook,
    description: 'Create dynamic webhook endpoints to receive events',
    color: 'text-blue-600'
  },
  { 
    value: 'http_client', 
    label: 'HTTP Client', 
    icon: Globe,
    description: 'Send events to external HTTP endpoints',
    color: 'text-green-600'
  },
  { 
    value: 'pubsub', 
    label: 'Pub/Sub', 
    icon: MessageSquare,
    description: 'Publish events to message queues and topics',
    color: 'text-purple-600'
  },
  { 
    value: 'kinesis', 
    label: 'Kinesis Stream', 
    icon: Database,
    description: 'Stream events to AWS Kinesis data streams',
    color: 'text-orange-600'
  },
  { 
    value: 'pagerduty', 
    label: 'PagerDuty', 
    icon: AlertTriangle,
    description: 'Send events to PagerDuty for incident management',
    color: 'text-red-600'
  },
  { 
    value: 'nats', 
    label: 'NATS', 
    icon: Zap,
    description: 'Publish events to NATS messaging system',
    color: 'text-indigo-600'
  },
]

export function EventSubscriptions() {
  const [inputSources, setInputSources] = useState<InputSourceConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [selectedSource, setSelectedSource] = useState<InputSourceConfig | null>(null)
  const [testingSource, setTestingSource] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    type: 'webhook' as InputSourceType,
    name: '',
    description: '',
    enabled: true,
    config: {} as Record<string, any>
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      await Promise.all([
        eventsApi.getEventSubscriptions()
      ])
      // Transform existing subscriptions to new format or start with empty array
      setInputSources([])
    } catch (error) {
      console.error('Failed to load data:', error)
      showToast('Failed to load input sources', 'error')
    } finally {
      setLoading(false)
    }
  }

  const resetForm = () => {
    setFormData({
      type: 'webhook',
      name: '',
      description: '',
      enabled: true,
      config: {}
    })
  }

  const getDefaultConfig = (type: InputSourceType) => {
    switch (type) {
      case 'webhook':
        return {
          endpoint: '/webhook/events',
          port: 8080,
          authentication: 'none',
          ssl_enabled: false,
          rate_limit: 1000
        }
      case 'http_client':
        return {
          target_url: '',
          method: 'POST',
          headers: {},
          timeout: 30,
          retry_count: 3
        }
      case 'pubsub':
        return {
          topic: '',
          project_id: '',
          credentials: {},
          region: 'us-central1'
        }
      case 'kinesis':
        return {
          stream_name: '',
          region: 'us-east-1',
          partition_key: '',
          credentials: {}
        }
      case 'pagerduty':
        return {
          api_key: '',
          service_id: '',
          escalation_policy: '',
          urgency: 'high'
        }
      case 'nats':
        return {
          server_url: 'nats://localhost:4222',
          subject: 'events',
          cluster: '',
          credentials: {}
        }
      default:
        return {}
    }
  }

  const handleCreate = () => {
    resetForm()
    setIsCreateDialogOpen(true)
  }

  const handleEdit = (source: InputSourceConfig) => {
    setFormData({
      type: source.type,
      name: source.name,
      description: source.description || '',
      enabled: source.enabled,
      config: { ...source.config }
    })
    setSelectedSource(source)
    setIsEditDialogOpen(true)
  }

  const handleDelete = async (_sourceName: string) => {
    if (!confirm('Are you sure you want to delete this input source?')) return

    try {
      // await eventsApi.deleteEventSubscription(_sourceName)
      showToast('Input source deleted successfully')
      loadData()
    } catch (error) {
      console.error('Failed to delete input source:', error)
      showToast('Failed to delete input source', 'error')
    }
  }

  const handleTestSource = async (sourceId: string) => {
    try {
      setTestingSource(sourceId)
      // await eventsApi.testEventSubscription(sourceId)
      showToast('Test event sent successfully')
    } catch (error) {
      console.error('Failed to test input source:', error)
      showToast('Failed to test input source', 'error')
    } finally {
      setTestingSource(null)
    }
  }

  const handleSubmit = async () => {
    try {
      if (isEditDialogOpen && selectedSource) {
        // await eventsApi.updateEventSubscription(selectedSource.name, formData)
        showToast('Input source updated successfully')
      } else {
        // await eventsApi.createEventSubscription(formData)
        showToast('Input source created successfully')
      }

      setIsCreateDialogOpen(false)
      setIsEditDialogOpen(false)
      setSelectedSource(null)
      resetForm()
      loadData()
    } catch (error) {
      console.error('Failed to save input source:', error)
      showToast('Failed to save input source', 'error')
    }
  }

  const renderConfigFields = () => {
    const { type, config } = formData

    switch (type) {
      case 'webhook':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Endpoint Path</label>
              <input
                type="text"
                value={config.endpoint || ''}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, endpoint: e.target.value } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="/webhook/events"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Port</label>
              <input
                type="number"
                value={config.port || ''}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, port: parseInt(e.target.value) } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="8080"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Authentication</label>
              <select
                value={config.authentication || 'none'}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, authentication: e.target.value } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="none">None</option>
                <option value="basic">Basic Auth</option>
                <option value="bearer">Bearer Token</option>
                <option value="api_key">API Key</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">SSL Enabled</label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={config.ssl_enabled || false}
                  onChange={(e) => setFormData(prev => ({ 
                    ...prev, 
                    config: { ...prev.config, ssl_enabled: e.target.checked } 
                  }))}
                  className="mr-2"
                />
                Enable SSL/TLS
              </label>
            </div>
          </div>
        )

      case 'http_client':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Target URL</label>
              <input
                type="url"
                value={config.target_url || ''}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, target_url: e.target.value } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="https://api.example.com/events"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">HTTP Method</label>
              <select
                value={config.method || 'POST'}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, method: e.target.value } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="PATCH">PATCH</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Timeout (seconds)</label>
              <input
                type="number"
                value={config.timeout || 30}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, timeout: parseInt(e.target.value) } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
                max="300"
              />
            </div>
          </div>
        )

      case 'pubsub':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Topic Name</label>
              <input
                type="text"
                value={config.topic || ''}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, topic: e.target.value } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="cloud-events"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Project ID</label>
              <input
                type="text"
                value={config.project_id || ''}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, project_id: e.target.value } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="your-gcp-project-id"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Region</label>
              <input
                type="text"
                value={config.region || 'us-central1'}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, region: e.target.value } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="us-central1"
              />
            </div>
          </div>
        )

      case 'kinesis':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Stream Name</label>
              <input
                type="text"
                value={config.stream_name || ''}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, stream_name: e.target.value } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="cloud-events-stream"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">AWS Region</label>
              <input
                type="text"
                value={config.region || 'us-east-1'}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, region: e.target.value } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="us-east-1"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Partition Key</label>
              <input
                type="text"
                value={config.partition_key || ''}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, partition_key: e.target.value } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="event-type"
              />
            </div>
          </div>
        )

      case 'pagerduty':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
              <input
                type="password"
                value={config.api_key || ''}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, api_key: e.target.value } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="PAGERDUTY_API_KEY"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Service ID</label>
              <input
                type="text"
                value={config.service_id || ''}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, service_id: e.target.value } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="PAGERDUTY_SERVICE_ID"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Urgency</label>
              <select
                value={config.urgency || 'high'}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, urgency: e.target.value } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="low">Low</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>
        )

      case 'nats':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Server URL</label>
              <input
                type="text"
                value={config.server_url || 'nats://localhost:4222'}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, server_url: e.target.value } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="nats://localhost:4222"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Subject</label>
              <input
                type="text"
                value={config.subject || ''}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, subject: e.target.value } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="cloud.events"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Cluster Name</label>
              <input
                type="text"
                value={config.cluster || ''}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  config: { ...prev.config, cluster: e.target.value } 
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="audit-cluster"
              />
            </div>
          </div>
        )

      default:
        return null
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading input sources...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Event Input Sources</h2>
          <p className="text-gray-600 mt-1">
            Configure input sources for receiving and processing cloud events
          </p>
        </div>
        <button
          onClick={handleCreate}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Input Source
        </button>
      </div>

      {/* Input Sources List */}
      <div className="grid gap-6">
        {inputSources.length === 0 ? (
          <div className="bg-white shadow rounded-lg p-6">
            <div className="text-center py-12">
              <Bell className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No input sources configured</h3>
              <p className="text-gray-600 mb-4">
                Create your first input source to start receiving cloud events
              </p>
              <button
                onClick={handleCreate}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                Create Input Source
              </button>
            </div>
          </div>
        ) : (
          inputSources.map((source) => {
            const sourceType = INPUT_SOURCE_TYPES.find(t => t.value === source.type)
            const IconComponent = sourceType?.icon || Bell
            
            return (
              <div key={source.name} className="bg-white shadow rounded-lg p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center space-x-3">
                    <IconComponent className={`w-6 h-6 ${sourceType?.color || 'text-gray-600'}`} />
                    <div>
                      <h3 className="text-lg font-semibold">{source.name}</h3>
                      <p className="text-gray-600">{source.description}</p>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {sourceType?.label}
                      </span>
                    </div>
                  </div>
                  <div className="flex space-x-1">
                    <button
                      className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                      onClick={() => handleTestSource(source.name)}
                      disabled={testingSource === source.name}
                      title="Test Input Source"
                    >
                      <TestTube className="w-4 h-4" />
                    </button>
                    <button
                      className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                      onClick={() => handleEdit(source)}
                      title="Edit Input Source"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                      onClick={() => handleDelete(source.name)}
                      title="Delete Input Source"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Status:</span>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      source.enabled ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {source.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Type:</span>
                    <span className="text-sm font-medium">{sourceType?.description}</span>
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
                {isEditDialogOpen ? 'Edit Input Source' : 'Create Input Source'}
              </h2>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Input Source Type</label>
                <div className="grid grid-cols-2 gap-3">
                  {INPUT_SOURCE_TYPES.map(type => {
                    const IconComponent = type.icon
                    return (
                      <label
                        key={type.value}
                        className={`relative flex cursor-pointer rounded-lg border p-4 ${
                          formData.type === type.value
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-300 hover:border-gray-400'
                        }`}
                      >
                        <input
                          type="radio"
                          name="source-type"
                          value={type.value}
                          checked={formData.type === type.value}
                          onChange={(e) => {
                            setFormData(prev => ({ 
                              ...prev, 
                              type: e.target.value as InputSourceType,
                              config: getDefaultConfig(e.target.value as InputSourceType)
                            }))
                          }}
                          className="sr-only"
                        />
                        <div className="flex items-center space-x-3">
                          <IconComponent className={`w-5 h-5 ${type.color}`} />
                          <div>
                            <div className="text-sm font-medium text-gray-900">{type.label}</div>
                            <div className="text-xs text-gray-500">{type.description}</div>
                          </div>
                        </div>
                      </label>
                    )
                  })}
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter input source name"
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

              {/* Dynamic configuration fields based on type */}
              {renderConfigFields()}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Enabled</label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.enabled}
                    onChange={(e) => setFormData(prev => ({ ...prev, enabled: e.target.checked }))}
                    className="mr-2"
                  />
                  Enable this input source
                </label>
              </div>
            </div>
            <div className="flex justify-end space-x-2 mt-6">
              <button
                onClick={() => {
                  setIsCreateDialogOpen(false)
                  setIsEditDialogOpen(false)
                  setSelectedSource(null)
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
