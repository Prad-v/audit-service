import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Activity, FileText, Plus, Clock, BookOpen, Database, Zap, MessageSquare } from 'lucide-react'
import { auditApi, type AuditEvent } from '@/lib/api'

export function Dashboard() {
  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: auditApi.getHealth,
  })

  const { data: eventsData } = useQuery({
    queryKey: ['events', { page: 1, size: 5 }],
    queryFn: () => auditApi.getEvents({ page: 1, size: 5 }),
  })

  const stats = [
    {
      name: 'Total Events',
      value: eventsData?.total_count || 0,
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      name: 'Recent Events',
      value: eventsData?.items?.length || 0,
      icon: Clock,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      name: 'Service Status',
      value: healthData?.status === 'healthy' ? 'Healthy' : 'Unhealthy',
      icon: Activity,
      color: healthData?.status === 'healthy' ? 'text-green-600' : 'text-red-600',
      bgColor: healthData?.status === 'healthy' ? 'bg-green-100' : 'bg-red-100',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Welcome to the Audit Log Framework dashboard</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat) => (
          <div key={stat.name} className="card">
            <div className="flex items-center">
              <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`h-6 w-6 ${stat.color}`} />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Detailed Health Status */}
      {healthData && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">System Health Details</h2>
          <div className="space-y-4">
            {/* Overall Status */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center">
                <Activity className="h-6 w-6 text-gray-600 mr-3" />
                <div>
                  <h3 className="font-medium text-gray-900">Overall Status</h3>
                  <p className="text-sm text-gray-500">System health overview</p>
                </div>
              </div>
              <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                healthData.status === 'healthy' ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100'
              }`}>
                {healthData.status}
              </div>
            </div>

            {/* Service Status */}
            {healthData.services && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(healthData.services).map(([service, status]) => {
                  const getServiceIcon = (serviceName: string) => {
                    switch (serviceName) {
                      case 'database':
                        return Database
                      case 'redis':
                        return Zap
                      case 'nats':
                        return MessageSquare
                      default:
                        return Activity
                    }
                  }
                  const Icon = getServiceIcon(service)
                  
                  return (
                    <div key={service} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                      <div className="flex items-center">
                        <Icon className="h-5 w-5 text-gray-600 mr-3" />
                        <div>
                          <h3 className="font-medium text-gray-900 capitalize">{service}</h3>
                          <p className="text-sm text-gray-500">Service status</p>
                        </div>
                      </div>
                      <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        status === 'healthy' ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100'
                      }`}>
                        {String(status)}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
            
            {/* Fallback when services data is not available */}
            {!healthData.services && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex items-center">
                  <Activity className="h-5 w-5 text-yellow-600 mr-3" />
                  <div>
                    <h3 className="font-medium text-yellow-900">Service Status</h3>
                    <p className="text-sm text-yellow-700">Detailed service status information is not available</p>
                  </div>
                </div>
              </div>
            )}

            {/* Version Info */}
            <div className="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
              <div>
                <h3 className="font-medium text-gray-900">Version</h3>
                <p className="text-sm text-gray-500">Current system version</p>
              </div>
              <span className="text-sm font-medium text-blue-600">{healthData.version}</span>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/audit-logs"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <FileText className="h-8 w-8 text-blue-600 mr-4" />
            <div>
              <h3 className="font-medium text-gray-900">View Audit Logs</h3>
              <p className="text-sm text-gray-600">Browse and search through audit events</p>
            </div>
          </Link>
          <Link
            to="/create-event"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Plus className="h-8 w-8 text-green-600 mr-4" />
            <div>
              <h3 className="font-medium text-gray-900">Create Event</h3>
              <p className="text-sm text-gray-600">Manually create a new audit event</p>
            </div>
          </Link>
          <a
            href={`${window.location.origin}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <BookOpen className="h-8 w-8 text-purple-600 mr-4" />
            <div>
              <h3 className="font-medium text-gray-900">Documentation</h3>
              <p className="text-sm text-gray-600">View API documentation</p>
            </div>
          </a>
        </div>
      </div>

      {/* Recent Events */}
      {eventsData?.items && eventsData.items.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Events</h2>
            <Link to="/audit-logs" className="text-primary-600 hover:text-primary-700 text-sm font-medium">
              View all
            </Link>
          </div>
          <div className="space-y-3">
            {eventsData.items.slice(0, 5).map((event: AuditEvent) => (
              <div key={event.audit_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(event.status)}`}>
                    {event.status}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{event.event_type}</p>
                    <p className="text-sm text-gray-600">{event.action}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600">{formatRelativeTime(event.timestamp)}</p>
                  <p className="text-xs text-gray-500">{event.user_id || 'System'}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function getStatusColor(status: string) {
  switch (status.toLowerCase()) {
    case 'success':
      return 'text-green-600 bg-green-100'
    case 'error':
      return 'text-red-600 bg-red-100'
    case 'warning':
      return 'text-yellow-600 bg-yellow-100'
    case 'info':
      return 'text-blue-600 bg-blue-100'
    default:
      return 'text-gray-600 bg-gray-100'
  }
}

function formatRelativeTime(date: string | Date) {
  const now = new Date()
  const targetDate = new Date(date)
  const diffInSeconds = Math.floor((now.getTime() - targetDate.getTime()) / 1000)

  if (diffInSeconds < 60) {
    return `${diffInSeconds}s ago`
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60)
    return `${minutes}m ago`
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600)
    return `${hours}h ago`
  } else {
    const days = Math.floor(diffInSeconds / 86400)
    return `${days}d ago`
  }
}
