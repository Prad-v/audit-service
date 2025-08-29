import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Save, ArrowLeft } from 'lucide-react'
import { auditApi } from '@/lib/api'
import { Link } from 'react-router-dom'

export function CreateEvent() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState({
    event_type: '',
    user_id: '',
    session_id: '',
    ip_address: '',
    user_agent: '',
    resource_type: '',
    resource_id: '',
    action: '',
    status: 'success',
    request_data: '',
    response_data: '',
    metadata: '',
    tenant_id: 'default',
    service_name: 'audit-service',
    correlation_id: '',
    retention_period_days: 90,
  })

  const createEventMutation = useMutation({
    mutationFn: auditApi.createEvent,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['events'] })
      navigate('/audit-logs')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    const eventData = {
      ...formData,
      request_data: formData.request_data ? JSON.parse(formData.request_data) : undefined,
      response_data: formData.response_data ? JSON.parse(formData.response_data) : undefined,
      metadata: formData.metadata ? JSON.parse(formData.metadata) : undefined,
    }

    createEventMutation.mutate(eventData)
  }

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Link
          to="/audit-logs"
          className="flex items-center text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Audit Logs
        </Link>
      </div>

      <div>
        <h1 className="text-2xl font-bold text-gray-900">Create Audit Event</h1>
        <p className="text-gray-600">Manually create a new audit event</p>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Event Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Event Type *
            </label>
            <input
              type="text"
              required
              value={formData.event_type}
              onChange={(e) => handleChange('event_type', e.target.value)}
              className="input-field"
              placeholder="e.g., user_login"
            />
          </div>

          {/* Action */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Action *
            </label>
            <input
              type="text"
              required
              value={formData.action}
              onChange={(e) => handleChange('action', e.target.value)}
              className="input-field"
              placeholder="e.g., login"
            />
          </div>

          {/* User ID */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              User ID
            </label>
            <input
              type="text"
              value={formData.user_id}
              onChange={(e) => handleChange('user_id', e.target.value)}
              className="input-field"
              placeholder="e.g., user123"
            />
          </div>

          {/* Session ID */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Session ID
            </label>
            <input
              type="text"
              value={formData.session_id}
              onChange={(e) => handleChange('session_id', e.target.value)}
              className="input-field"
              placeholder="e.g., session_456"
            />
          </div>

          {/* IP Address */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              IP Address
            </label>
            <input
              type="text"
              value={formData.ip_address}
              onChange={(e) => handleChange('ip_address', e.target.value)}
              className="input-field"
              placeholder="e.g., 192.168.1.100"
            />
          </div>

          {/* User Agent */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              User Agent
            </label>
            <input
              type="text"
              value={formData.user_agent}
              onChange={(e) => handleChange('user_agent', e.target.value)}
              className="input-field"
              placeholder="e.g., Mozilla/5.0..."
            />
          </div>

          {/* Resource Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Resource Type
            </label>
            <input
              type="text"
              value={formData.resource_type}
              onChange={(e) => handleChange('resource_type', e.target.value)}
              className="input-field"
              placeholder="e.g., file"
            />
          </div>

          {/* Resource ID */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Resource ID
            </label>
            <input
              type="text"
              value={formData.resource_id}
              onChange={(e) => handleChange('resource_id', e.target.value)}
              className="input-field"
              placeholder="e.g., file_123"
            />
          </div>

          {/* Status */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={formData.status}
              onChange={(e) => handleChange('status', e.target.value)}
              className="input-field"
            >
              <option value="success">Success</option>
              <option value="error">Error</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
            </select>
          </div>

          {/* Correlation ID */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Correlation ID
            </label>
            <input
              type="text"
              value={formData.correlation_id}
              onChange={(e) => handleChange('correlation_id', e.target.value)}
              className="input-field"
              placeholder="e.g., correlation_123"
            />
          </div>

          {/* Retention Period */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Retention Period (days)
            </label>
            <input
              type="number"
              min="1"
              max="2555"
              value={formData.retention_period_days}
              onChange={(e) => handleChange('retention_period_days', e.target.value)}
              className="input-field"
            />
          </div>
        </div>

        {/* JSON Fields */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Request Data (JSON)
            </label>
            <textarea
              value={formData.request_data}
              onChange={(e) => handleChange('request_data', e.target.value)}
              className="input-field h-24"
              placeholder='{"key": "value"}'
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Response Data (JSON)
            </label>
            <textarea
              value={formData.response_data}
              onChange={(e) => handleChange('response_data', e.target.value)}
              className="input-field h-24"
              placeholder='{"key": "value"}'
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Metadata (JSON)
            </label>
            <textarea
              value={formData.metadata}
              onChange={(e) => handleChange('metadata', e.target.value)}
              className="input-field h-24"
              placeholder='{"key": "value"}'
            />
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end space-x-4">
          <Link
            to="/audit-logs"
            className="btn-secondary"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={createEventMutation.isPending}
            className="btn-primary flex items-center"
          >
            <Save className="h-4 w-4 mr-2" />
            {createEventMutation.isPending ? 'Creating...' : 'Create Event'}
          </button>
        </div>

        {createEventMutation.isError && (
          <div className="text-red-600 text-sm">
            Error creating event: {createEventMutation.error?.message}
          </div>
        )}
      </form>
    </div>
  )
}
