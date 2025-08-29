import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, Bell, CheckCircle, XCircle, TestTube } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AlertProvider {
  provider_id: string
  name: string
  provider_type: 'pagerduty' | 'slack' | 'webhook' | 'email'
  enabled: boolean
  config: Record<string, any>
  tenant_id: string
  created_by: string
  created_at: string
  updated_at: string
}

interface AlertProviderCreate {
  name: string
  provider_type: 'pagerduty' | 'slack' | 'webhook' | 'email'
  enabled: boolean
  config: Record<string, any>
}

export function AlertProviders() {
  const [providers, setProviders] = useState<AlertProvider[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  // TODO: Implement edit functionality
  // const [editingProvider, setEditingProvider] = useState<AlertProvider | null>(null)
  const [formData, setFormData] = useState<AlertProviderCreate>({
    name: '',
    provider_type: 'slack',
    enabled: true,
    config: {}
  })

  useEffect(() => {
    fetchProviders()
  }, [])

  const fetchProviders = async () => {
    try {
      const response = await fetch('/api/v1/alerts/providers', {
        headers: {
          'Authorization': 'Bearer test-token'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setProviders(data.providers || [])
      }
    } catch (error) {
      console.error('Failed to fetch providers:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateProvider = async () => {
    try {
      const response = await fetch('/api/v1/alerts/providers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token'
        },
        body: JSON.stringify(formData)
      })
      if (response.ok) {
        setShowCreateModal(false)
        setFormData({
          name: '',
          provider_type: 'slack',
          enabled: true,
          config: {}
        })
        fetchProviders()
      }
    } catch (error) {
      console.error('Failed to create provider:', error)
    }
  }

  const handleDeleteProvider = async (providerId: string) => {
    if (!confirm('Are you sure you want to delete this provider?')) return
    
    try {
      const response = await fetch(`/api/v1/alerts/providers/${providerId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': 'Bearer test-token'
        }
      })
      if (response.ok) {
        fetchProviders()
      }
    } catch (error) {
      console.error('Failed to delete provider:', error)
    }
  }

  const handleTestProvider = async (providerId: string) => {
    try {
      const response = await fetch(`/api/v1/alerts/providers/${providerId}/test`, {
        method: 'POST',
        headers: {
          'Authorization': 'Bearer test-token'
        }
      })
      if (response.ok) {
        alert('Test message sent successfully!')
      } else {
        alert('Failed to send test message')
      }
    } catch (error) {
      console.error('Failed to test provider:', error)
      alert('Failed to test provider')
    }
  }

  const getProviderIcon = (type: string) => {
    switch (type) {
      case 'pagerduty':
        return '🔴'
      case 'slack':
        return '💬'
      case 'webhook':
        return '🔗'
      case 'email':
        return '📧'
      default:
        return '🔔'
    }
  }

  const getProviderColor = (type: string) => {
    switch (type) {
      case 'pagerduty':
        return 'text-red-600 bg-red-100'
      case 'slack':
        return 'text-blue-600 bg-blue-100'
      case 'webhook':
        return 'text-purple-600 bg-purple-100'
      case 'email':
        return 'text-green-600 bg-green-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alert Providers</h1>
          <p className="text-gray-600">Configure notification channels for alerts</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Provider
        </button>
      </div>

      {/* Providers Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {providers.map((provider) => (
          <div key={provider.provider_id} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <span className="text-2xl">{getProviderIcon(provider.provider_type)}</span>
                </div>
                <div className="ml-4 flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-medium text-gray-900">{provider.name}</h3>
                    <span className={cn('px-2 py-1 text-xs font-medium rounded-full', getProviderColor(provider.provider_type))}>
                      {provider.provider_type}
                    </span>
                  </div>
                  <div className="flex items-center mt-2">
                    {provider.enabled ? (
                      <CheckCircle className="w-4 h-4 text-green-500 mr-1" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-500 mr-1" />
                    )}
                    <span className={cn('text-sm', provider.enabled ? 'text-green-600' : 'text-red-600')}>
                      {provider.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="mt-4 flex items-center justify-between">
                <div className="text-sm text-gray-500">
                  Created {new Date(provider.created_at).toLocaleDateString()}
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleTestProvider(provider.provider_id)}
                    className="text-gray-400 hover:text-blue-600"
                    title="Test Provider"
                  >
                    <TestTube className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => {/* TODO: Implement edit functionality */}}
                    className="text-gray-400 hover:text-gray-600"
                    title="Edit Provider (Coming Soon)"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteProvider(provider.provider_id)}
                    className="text-gray-400 hover:text-red-600"
                    title="Delete Provider"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {providers.length === 0 && (
        <div className="text-center py-12">
          <Bell className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No providers</h3>
          <p className="mt-1 text-sm text-gray-500">Get started by adding a notification provider.</p>
          <div className="mt-6">
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Provider
            </button>
          </div>
        </div>
      )}

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Add Alert Provider</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Name</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Provider Type</label>
                  <select
                    value={formData.provider_type}
                    onChange={(e) => setFormData({ ...formData, provider_type: e.target.value as any })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="slack">Slack</option>
                    <option value="pagerduty">PagerDuty</option>
                    <option value="webhook">Webhook</option>
                    <option value="email">Email</option>
                  </select>
                </div>
                
                {/* Provider-specific configuration fields */}
                {formData.provider_type === 'slack' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Webhook URL</label>
                    <input
                      type="url"
                      value={formData.config.webhook_url || ''}
                      onChange={(e) => setFormData({ 
                        ...formData, 
                        config: { ...formData.config, webhook_url: e.target.value }
                      })}
                      placeholder="https://hooks.slack.com/services/..."
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                )}
                
                {formData.provider_type === 'pagerduty' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">API Key</label>
                      <input
                        type="password"
                        value={formData.config.api_key || ''}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          config: { ...formData.config, api_key: e.target.value }
                        })}
                        placeholder="PagerDuty API Key"
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Service ID</label>
                      <input
                        type="text"
                        value={formData.config.service_id || ''}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          config: { ...formData.config, service_id: e.target.value }
                        })}
                        placeholder="PagerDuty Service ID"
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                  </>
                )}
                
                {formData.provider_type === 'webhook' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Webhook URL</label>
                    <input
                      type="url"
                      value={formData.config.url || ''}
                      onChange={(e) => setFormData({ 
                        ...formData, 
                        config: { ...formData.config, url: e.target.value }
                      })}
                      placeholder="https://your-webhook-endpoint.com"
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                    />
                  </div>
                )}
                
                {formData.provider_type === 'email' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">SMTP Host</label>
                      <input
                        type="text"
                        value={formData.config.smtp_host || ''}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          config: { ...formData.config, smtp_host: e.target.value }
                        })}
                        placeholder="smtp.gmail.com"
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700">To Email</label>
                      <input
                        type="email"
                        value={formData.config.to_emails || ''}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          config: { ...formData.config, to_emails: e.target.value }
                        })}
                        placeholder="alerts@yourcompany.com"
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                      />
                    </div>
                  </>
                )}
                
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.enabled}
                    onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 block text-sm text-gray-900">Enabled</label>
                </div>
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateProvider}
                  className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700"
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
