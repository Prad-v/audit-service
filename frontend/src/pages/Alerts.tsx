import { useState, useEffect } from 'react'
import { Eye, CheckCircle, XCircle, Clock, AlertTriangle, Filter } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Alert {
  alert_id: string
  policy_id: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  status: 'active' | 'resolved' | 'acknowledged' | 'suppressed'
  title: string
  message: string
  summary: string
  triggered_at: string
  resolved_at?: string
  acknowledged_at?: string
  acknowledged_by?: string
  delivery_status: Record<string, string>
  tenant_id: string
  created_at: string
  updated_at: string
}

export function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filters, setFilters] = useState({
    severity: '',
    status: '',
    policy_id: ''
  })

  useEffect(() => {
    fetchAlerts()
  }, [filters])

  const fetchAlerts = async () => {
    try {
      const params = new URLSearchParams()
      if (filters.severity) params.append('severity', filters.severity)
      if (filters.status) params.append('status', filters.status)
      if (filters.policy_id) params.append('policy_id', filters.policy_id)

      const response = await fetch(`/api/v1/alerts/alerts?${params}`, {
        headers: {
          'Authorization': 'Bearer test-token'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setAlerts(data.alerts || [])
      }
    } catch (error) {
      console.error('Failed to fetch alerts:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/v1/alerts/alerts/${alertId}/acknowledge`, {
        method: 'PUT',
        headers: {
          'Authorization': 'Bearer test-token'
        }
      })
      if (response.ok) {
        fetchAlerts()
      }
    } catch (error) {
      console.error('Failed to acknowledge alert:', error)
    }
  }

  const handleResolveAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/v1/alerts/alerts/${alertId}/resolve`, {
        method: 'PUT',
        headers: {
          'Authorization': 'Bearer test-token'
        }
      })
      if (response.ok) {
        fetchAlerts()
      }
    } catch (error) {
      console.error('Failed to resolve alert:', error)
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-red-600 bg-red-100'
      case 'acknowledged':
        return 'text-yellow-600 bg-yellow-100'
      case 'resolved':
        return 'text-green-600 bg-green-100'
      case 'suppressed':
        return 'text-gray-600 bg-gray-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <AlertTriangle className="w-4 h-4" />
      case 'acknowledged':
        return <Clock className="w-4 h-4" />
      case 'resolved':
        return <CheckCircle className="w-4 h-4" />
      case 'suppressed':
        return <XCircle className="w-4 h-4" />
      default:
        return <AlertTriangle className="w-4 h-4" />
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
          <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
          <p className="text-gray-600">View and manage triggered alerts</p>
        </div>
        <div className="text-sm text-gray-500">
          {alerts.length} alerts
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <div className="flex items-center mb-4">
          <Filter className="w-4 h-4 mr-2 text-gray-500" />
          <h3 className="text-sm font-medium text-gray-900">Filters</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
            <select
              value={filters.severity}
              onChange={(e) => setFilters({ ...filters, severity: e.target.value })}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
              <option value="info">Info</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="resolved">Resolved</option>
              <option value="suppressed">Suppressed</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Policy ID</label>
            <input
              type="text"
              value={filters.policy_id}
              onChange={(e) => setFilters({ ...filters, policy_id: e.target.value })}
              placeholder="Filter by policy ID"
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {alerts.map((alert) => (
            <li key={alert.alert_id} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    {getStatusIcon(alert.status)}
                  </div>
                  <div className="ml-4">
                    <div className="flex items-center">
                      <h3 className="text-sm font-medium text-gray-900">{alert.title}</h3>
                      <span className={cn('ml-2 px-2 py-1 text-xs font-medium rounded-full', getSeverityColor(alert.severity))}>
                        {alert.severity}
                      </span>
                      <span className={cn('ml-2 px-2 py-1 text-xs font-medium rounded-full', getStatusColor(alert.status))}>
                        {alert.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 mt-1">{alert.summary}</p>
                    <div className="flex items-center mt-2 text-xs text-gray-500">
                      <Clock className="w-3 h-3 mr-1" />
                      Triggered {new Date(alert.triggered_at).toLocaleString()}
                      {alert.acknowledged_at && (
                        <>
                          <span className="mx-2">•</span>
                          Acknowledged {new Date(alert.acknowledged_at).toLocaleString()}
                        </>
                      )}
                      {alert.resolved_at && (
                        <>
                          <span className="mx-2">•</span>
                          Resolved {new Date(alert.resolved_at).toLocaleString()}
                        </>
                      )}
                    </div>
                    {Object.keys(alert.delivery_status).length > 0 && (
                      <div className="flex items-center mt-2 text-xs text-gray-500">
                        <span className="mr-2">Delivery:</span>
                        {Object.entries(alert.delivery_status).map(([provider, status]) => (
                          <span key={provider} className={cn('mr-2 px-1 py-0.5 rounded', 
                            status === 'sent' ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100'
                          )}>
                            {provider}: {status}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {alert.status === 'active' && (
                    <>
                      <button
                        onClick={() => handleAcknowledgeAlert(alert.alert_id)}
                        className="text-gray-400 hover:text-yellow-600"
                        title="Acknowledge Alert"
                      >
                        <Clock className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleResolveAlert(alert.alert_id)}
                        className="text-gray-400 hover:text-green-600"
                        title="Resolve Alert"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </button>
                    </>
                  )}
                  <button
                    className="text-gray-400 hover:text-gray-600"
                    title="View Details"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
        {alerts.length === 0 && (
          <div className="text-center py-12">
            <AlertTriangle className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No alerts</h3>
            <p className="mt-1 text-sm text-gray-500">
              {Object.values(filters).some(f => f) ? 'No alerts match your filters.' : 'No alerts have been triggered yet.'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
