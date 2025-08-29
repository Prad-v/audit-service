import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Activity, FileText, Plus, Clock, BookOpen, Database, Zap, MessageSquare, TrendingUp, BarChart3, Cpu, HardDrive } from 'lucide-react'
import { auditApi, type AuditEvent, type TopEventType } from '@/lib/api'

export function Dashboard() {
  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: auditApi.getHealth,
  })

  const { data: eventsData } = useQuery({
    queryKey: ['events', { page: 1, size: 5 }],
    queryFn: () => auditApi.getEvents({ page: 1, size: 5 }),
  })

  const { data: metricsData } = useQuery({
    queryKey: ['metrics'],
    queryFn: auditApi.getMetrics,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const { data: topEventTypes } = useQuery({
    queryKey: ['top-event-types'],
    queryFn: () => auditApi.getTopEventTypes(10),
    refetchInterval: 60000, // Refresh every minute
  })

  const { data: systemMetrics } = useQuery({
    queryKey: ['system-metrics'],
    queryFn: auditApi.getSystemMetrics,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const stats = [
    {
      name: 'Total Events',
      value: metricsData?.metrics?.total_events || eventsData?.total_count || 0,
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      name: 'Events Today',
      value: metricsData?.metrics?.events_today || 0,
      icon: Clock,
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      name: 'Ingestion Rate',
      value: `${(metricsData?.metrics?.ingestion_rate || 0).toFixed(1)}/min`,
      icon: TrendingUp,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      name: 'Query Rate',
      value: `${(metricsData?.metrics?.query_rate || 0).toFixed(1)}/min`,
      icon: BarChart3,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
    {
      name: 'Avg Response Time',
      value: `${(metricsData?.metrics?.avg_response_time || 0).toFixed(0)}ms`,
      icon: Activity,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-100',
    },
    {
      name: 'Error Rate',
      value: `${(metricsData?.metrics?.error_rate || 0).toFixed(2)}%`,
      icon: Activity,
      color: metricsData?.metrics?.error_rate > 1 ? 'text-red-600' : 'text-yellow-600',
      bgColor: metricsData?.metrics?.error_rate > 1 ? 'bg-red-100' : 'bg-yellow-100',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Welcome to the Audit Log Framework dashboard</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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

      {/* Top Event Types */}
      {topEventTypes && topEventTypes.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Event Types</h2>
          <div className="space-y-3">
            {topEventTypes.slice(0, 5).map((eventType: TopEventType, index: number) => (
              <div key={eventType.event_type} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-primary-600">{index + 1}</span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{eventType.event_type}</p>
                    <p className="text-sm text-gray-600">{eventType.count.toLocaleString()} events</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">{eventType.percentage.toFixed(1)}%</p>
                  <div className="w-20 bg-gray-200 rounded-full h-2 mt-1">
                    <div 
                      className="bg-primary-600 h-2 rounded-full" 
                      style={{ width: `${eventType.percentage}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* System Metrics */}
      {systemMetrics && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">System Performance</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center">
                <Cpu className="h-5 w-5 text-blue-600 mr-3" />
                <div>
                  <h3 className="font-medium text-gray-900">CPU Usage</h3>
                  <p className="text-sm text-gray-500">Current CPU utilization</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-lg font-semibold text-gray-900">{systemMetrics.cpu_usage.toFixed(1)}%</p>
                <div className="w-16 bg-gray-200 rounded-full h-2 mt-1">
                  <div 
                    className={`h-2 rounded-full ${systemMetrics.cpu_usage > 80 ? 'bg-red-500' : systemMetrics.cpu_usage > 60 ? 'bg-yellow-500' : 'bg-green-500'}`}
                    style={{ width: `${systemMetrics.cpu_usage}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center">
                <Activity className="h-5 w-5 text-green-600 mr-3" />
                <div>
                  <h3 className="font-medium text-gray-900">Memory Usage</h3>
                  <p className="text-sm text-gray-500">Current memory utilization</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-lg font-semibold text-gray-900">{systemMetrics.memory_usage.toFixed(1)}%</p>
                <div className="w-16 bg-gray-200 rounded-full h-2 mt-1">
                  <div 
                    className={`h-2 rounded-full ${systemMetrics.memory_usage > 80 ? 'bg-red-500' : systemMetrics.memory_usage > 60 ? 'bg-yellow-500' : 'bg-green-500'}`}
                    style={{ width: `${systemMetrics.memory_usage}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center">
                <HardDrive className="h-5 w-5 text-purple-600 mr-3" />
                <div>
                  <h3 className="font-medium text-gray-900">Disk Usage</h3>
                  <p className="text-sm text-gray-500">Current disk utilization</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-lg font-semibold text-gray-900">{systemMetrics.disk_usage.toFixed(1)}%</p>
                <div className="w-16 bg-gray-200 rounded-full h-2 mt-1">
                  <div 
                    className={`h-2 rounded-full ${systemMetrics.disk_usage > 80 ? 'bg-red-500' : systemMetrics.disk_usage > 60 ? 'bg-yellow-500' : 'bg-green-500'}`}
                    style={{ width: `${systemMetrics.disk_usage}%` }}
                  ></div>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center">
                <Database className="h-5 w-5 text-indigo-600 mr-3" />
                <div>
                  <h3 className="font-medium text-gray-900">Active Connections</h3>
                  <p className="text-sm text-gray-500">Database connections</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-lg font-semibold text-gray-900">{systemMetrics.active_connections}</p>
                <p className="text-sm text-gray-500">connections</p>
              </div>
            </div>

            <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center">
                <BarChart3 className="h-5 w-5 text-orange-600 mr-3" />
                <div>
                  <h3 className="font-medium text-gray-900">Database Size</h3>
                  <p className="text-sm text-gray-500">Current database size</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-lg font-semibold text-gray-900">{(systemMetrics.database_size / (1024 * 1024 * 1024)).toFixed(1)} GB</p>
                <p className="text-sm text-gray-500">total size</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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
          <a
            href="http://localhost:3001"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <BarChart3 className="h-8 w-8 text-teal-600 mr-4" />
            <div>
              <h3 className="font-medium text-gray-900">Grafana Dashboard</h3>
              <p className="text-sm text-gray-600">Advanced metrics and monitoring</p>
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
