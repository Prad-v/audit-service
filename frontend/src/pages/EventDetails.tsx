import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Calendar, User, Globe, FileText, Tag } from 'lucide-react'
import { auditApi } from '@/lib/api'
import { formatDate, getStatusColor } from '@/lib/utils'

export function EventDetails() {
  const { id } = useParams<{ id: string }>()

  const { data: event, isLoading, error } = useQuery({
    queryKey: ['event', id],
    queryFn: () => auditApi.getEvent(id!),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600">Loading event details...</div>
      </div>
    )
  }

  if (error || !event) {
    return (
      <div className="card">
        <div className="text-center text-red-600">
          Error loading event details. Please try again.
        </div>
      </div>
    )
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
        <h1 className="text-2xl font-bold text-gray-900">Event Details</h1>
        <p className="text-gray-600">Detailed information about this audit event</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Event Information */}
        <div className="lg:col-span-2 space-y-6">
          {/* Event Header */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(event.status)}`}>
                  {event.status}
                </div>
                <h2 className="text-xl font-semibold text-gray-900">{event.event_type}</h2>
              </div>
              <div className="text-sm text-gray-500">
                ID: {event.audit_id}
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Action</label>
                <p className="text-gray-900">{event.action}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Timestamp</label>
                <p className="text-gray-900">{formatDate(event.timestamp)}</p>
              </div>
            </div>
          </div>

          {/* User Information */}
          {(event.user_id || event.session_id || event.ip_address || event.user_agent) && (
            <div className="card">
              <div className="flex items-center space-x-2 mb-4">
                <User className="h-5 w-5 text-gray-500" />
                <h3 className="text-lg font-semibold text-gray-900">User Information</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {event.user_id && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">User ID</label>
                    <p className="text-gray-900">{event.user_id}</p>
                  </div>
                )}
                {event.session_id && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Session ID</label>
                    <p className="text-gray-900">{event.session_id}</p>
                  </div>
                )}
                {event.ip_address && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">IP Address</label>
                    <p className="text-gray-900">{event.ip_address}</p>
                  </div>
                )}
                {event.user_agent && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">User Agent</label>
                    <p className="text-gray-900 text-sm break-all">{event.user_agent}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Resource Information */}
          {(event.resource_type || event.resource_id) && (
            <div className="card">
              <div className="flex items-center space-x-2 mb-4">
                <FileText className="h-5 w-5 text-gray-500" />
                <h3 className="text-lg font-semibold text-gray-900">Resource Information</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {event.resource_type && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Resource Type</label>
                    <p className="text-gray-900">{event.resource_type}</p>
                  </div>
                )}
                {event.resource_id && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Resource ID</label>
                    <p className="text-gray-900">{event.resource_id}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Request/Response Data */}
          {(event.request_data || event.response_data) && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Request & Response Data</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {event.request_data && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Request Data</label>
                    <pre className="bg-gray-50 p-3 rounded-md text-sm overflow-x-auto">
                      {JSON.stringify(event.request_data, null, 2)}
                    </pre>
                  </div>
                )}
                {event.response_data && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Response Data</label>
                    <pre className="bg-gray-50 p-3 rounded-md text-sm overflow-x-auto">
                      {JSON.stringify(event.response_data, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Metadata */}
          {event.metadata && (
            <div className="card">
              <div className="flex items-center space-x-2 mb-4">
                <Tag className="h-5 w-5 text-gray-500" />
                <h3 className="text-lg font-semibold text-gray-900">Metadata</h3>
              </div>
              <pre className="bg-gray-50 p-3 rounded-md text-sm overflow-x-auto">
                {JSON.stringify(event.metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* System Information */}
          <div className="card">
            <div className="flex items-center space-x-2 mb-4">
              <Globe className="h-5 w-5 text-gray-500" />
              <h3 className="text-lg font-semibold text-gray-900">System Information</h3>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">Tenant ID</label>
                <p className="text-gray-900">{event.tenant_id}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Service Name</label>
                <p className="text-gray-900">{event.service_name}</p>
              </div>
              {event.correlation_id && (
                <div>
                  <label className="block text-sm font-medium text-gray-700">Correlation ID</label>
                  <p className="text-gray-900 text-sm break-all">{event.correlation_id}</p>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700">Retention Period</label>
                <p className="text-gray-900">{event.retention_period_days} days</p>
              </div>
            </div>
          </div>

          {/* Timestamps */}
          <div className="card">
            <div className="flex items-center space-x-2 mb-4">
              <Calendar className="h-5 w-5 text-gray-500" />
              <h3 className="text-lg font-semibold text-gray-900">Timestamps</h3>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">Event Time</label>
                <p className="text-gray-900 text-sm">{formatDate(event.timestamp)}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Created At</label>
                <p className="text-gray-900 text-sm">{formatDate(event.created_at)}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Partition Date</label>
                <p className="text-gray-900 text-sm">{event.partition_date}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
