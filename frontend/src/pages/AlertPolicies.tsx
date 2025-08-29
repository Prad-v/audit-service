import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, AlertTriangle, Clock, Users, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AlertRule {
  field: string
  operator: string
  value: string | number | boolean
  case_sensitive: boolean
}

interface TimeWindow {
  start_time: string
  end_time: string
  days_of_week: number[]
  timezone: string
}

interface AlertPolicy {
  policy_id: string
  name: string
  description?: string
  enabled: boolean
  rules: AlertRule[]
  match_all: boolean
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  message_template: string
  summary_template: string
  time_window?: TimeWindow
  throttle_minutes: number
  max_alerts_per_hour: number
  providers: string[]
  tenant_id: string
  created_by: string
  created_at: string
  updated_at: string
}

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

interface AlertPolicyCreate {
  name: string
  description?: string
  enabled: boolean
  rules: AlertRule[]
  match_all: boolean
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  message_template: string
  summary_template: string
  time_window?: TimeWindow
  throttle_minutes: number
  max_alerts_per_hour: number
  providers: string[]
}

export function AlertPolicies() {
  const [policies, setPolicies] = useState<AlertPolicy[]>([])
  const [providers, setProviders] = useState<AlertProvider[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingPolicy, setEditingPolicy] = useState<AlertPolicy | null>(null)
  const [formData, setFormData] = useState<AlertPolicyCreate>({
    name: '',
    description: '',
    enabled: true,
    rules: [],
    match_all: true,
    severity: 'medium',
    message_template: '',
    summary_template: '',
    throttle_minutes: 0,
    max_alerts_per_hour: 10,
    providers: []
  })

  useEffect(() => {
    fetchPolicies()
    fetchProviders()
  }, [])

  const fetchPolicies = async () => {
    try {
      const response = await fetch('/api/v1/alerts/policies', {
        headers: {
          'Authorization': 'Bearer test-token'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setPolicies(data.policies || [])
      }
    } catch (error) {
      console.error('Failed to fetch policies:', error)
    } finally {
      setIsLoading(false)
    }
  }

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
    }
  }

  const handleCreatePolicy = async () => {
    try {
      const response = await fetch('/api/v1/alerts/policies', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token'
        },
        body: JSON.stringify(formData)
      })
      if (response.ok) {
        setShowCreateModal(false)
        resetForm()
        fetchPolicies()
      }
    } catch (error) {
      console.error('Failed to create policy:', error)
    }
  }

  const handleUpdatePolicy = async () => {
    if (!editingPolicy) return
    
    try {
      const response = await fetch(`/api/v1/alerts/policies/${editingPolicy.policy_id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token'
        },
        body: JSON.stringify(formData)
      })
      if (response.ok) {
        setShowCreateModal(false)
        setEditingPolicy(null)
        resetForm()
        fetchPolicies()
      }
    } catch (error) {
      console.error('Failed to update policy:', error)
    }
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      enabled: true,
      rules: [],
      match_all: true,
      severity: 'medium',
      message_template: '',
      summary_template: '',
      throttle_minutes: 0,
      max_alerts_per_hour: 10,
      providers: []
    })
  }

  const handleEditPolicy = (policy: AlertPolicy) => {
    setEditingPolicy(policy)
    setFormData({
      name: policy.name,
      description: policy.description || '',
      enabled: policy.enabled,
      rules: policy.rules,
      match_all: policy.match_all,
      severity: policy.severity,
      message_template: policy.message_template,
      summary_template: policy.summary_template,
      time_window: policy.time_window,
      throttle_minutes: policy.throttle_minutes,
      max_alerts_per_hour: policy.max_alerts_per_hour,
      providers: policy.providers
    })
    setShowCreateModal(true)
  }

  const handleDeletePolicy = async (policyId: string) => {
    if (!confirm('Are you sure you want to delete this policy?')) return
    
    try {
      const response = await fetch(`/api/v1/alerts/policies/${policyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': 'Bearer test-token'
        }
      })
      if (response.ok) {
        fetchPolicies()
      }
    } catch (error) {
      console.error('Failed to delete policy:', error)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-600 bg-red-100'
      case 'high':
        return 'text-orange-600 bg-orange-100'
      case 'medium':
        return 'text-yellow-600 bg-yellow-100'
      case 'low':
        return 'text-blue-600 bg-blue-100'
      case 'info':
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
          <h1 className="text-2xl font-bold text-gray-900">Alert Policies</h1>
          <p className="text-gray-600">Manage alert policies and rules</p>
        </div>
        <button
          onClick={() => {
            setEditingPolicy(null)
            resetForm()
            setShowCreateModal(true)
          }}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Policy
        </button>
      </div>

      {/* Policies List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {policies.map((policy) => (
            <li key={policy.policy_id} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <AlertTriangle className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-4">
                    <div className="flex items-center">
                      <h3 className="text-sm font-medium text-gray-900">{policy.name}</h3>
                      <span className={cn('ml-2 px-2 py-1 text-xs font-medium rounded-full', getSeverityColor(policy.severity))}>
                        {policy.severity}
                      </span>
                      <span className={cn('ml-2 px-2 py-1 text-xs font-medium rounded-full', policy.enabled ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100')}>
                        {policy.enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                    {policy.description && (
                      <p className="text-sm text-gray-500 mt-1">{policy.description}</p>
                    )}
                    <div className="flex items-center mt-2 text-xs text-gray-500">
                      <Clock className="w-3 h-3 mr-1" />
                      {policy.throttle_minutes > 0 && `Throttle: ${policy.throttle_minutes}min`}
                      <Users className="w-3 h-3 ml-3 mr-1" />
                      {policy.providers.length} providers
                      <Settings className="w-3 h-3 ml-3 mr-1" />
                      {policy.rules.length} rules
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleEditPolicy(policy)}
                    className="text-gray-400 hover:text-gray-600"
                    title="Edit Policy"
                  >
                    <Edit className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDeletePolicy(policy.policy_id)}
                    className="text-gray-400 hover:text-red-600"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
        {policies.length === 0 && (
          <div className="text-center py-12">
            <AlertTriangle className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No policies</h3>
            <p className="mt-1 text-sm text-gray-500">Get started by creating a new alert policy.</p>
            <div className="mt-6">
              <button
                onClick={() => {
                  setEditingPolicy(null)
                  resetForm()
                  setShowCreateModal(true)
                }}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Policy
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-[600px] max-h-[90vh] overflow-y-auto shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                {editingPolicy ? 'Edit Alert Policy' : 'Create Alert Policy'}
              </h3>
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
                  <label className="block text-sm font-medium text-gray-700">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                    rows={3}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Severity</label>
                  <select
                    value={formData.severity}
                    onChange={(e) => setFormData({ ...formData, severity: e.target.value as any })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  >
                    <option value="info">Info</option>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Message Template</label>
                  <input
                    type="text"
                    value={formData.message_template}
                    onChange={(e) => setFormData({ ...formData, message_template: e.target.value })}
                    placeholder="e.g., Alert: {event_type} by {user_id}"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Summary Template</label>
                  <input
                    type="text"
                    value={formData.summary_template}
                    onChange={(e) => setFormData({ ...formData, summary_template: e.target.value })}
                    placeholder="e.g., Alert summary for {user_id}"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Alert Providers</label>
                  {providers.length > 0 ? (
                    <>
                      <select
                        multiple
                        value={formData.providers}
                        onChange={(e) => {
                          const selectedOptions = Array.from(e.target.selectedOptions, option => option.value)
                          setFormData({ ...formData, providers: selectedOptions })
                        }}
                        className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                      >
                        {providers.map(provider => (
                          <option key={provider.provider_id} value={provider.provider_id}>
                            {provider.name || 'Unnamed Provider'} ({provider.provider_type})
                          </option>
                        ))}
                      </select>
                      <p className="mt-1 text-sm text-gray-500">Hold Ctrl/Cmd to select multiple providers</p>
                    </>
                  ) : (
                    <div className="mt-1 p-2 bg-yellow-50 border border-yellow-200 rounded-md">
                      <p className="text-sm text-yellow-700">No providers available. Please create providers first.</p>
                    </div>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Throttle Minutes</label>
                  <input
                    type="number"
                    value={formData.throttle_minutes}
                    onChange={(e) => setFormData({ ...formData, throttle_minutes: parseInt(e.target.value) || 0 })}
                    min="0"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Max Alerts Per Hour</label>
                  <input
                    type="number"
                    value={formData.max_alerts_per_hour}
                    onChange={(e) => setFormData({ ...formData, max_alerts_per_hour: parseInt(e.target.value) || 10 })}
                    min="1"
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
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
                  onClick={() => {
                    setShowCreateModal(false)
                    setEditingPolicy(null)
                    resetForm()
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  onClick={editingPolicy ? handleUpdatePolicy : handleCreatePolicy}
                  className="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700"
                >
                  {editingPolicy ? 'Update' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
