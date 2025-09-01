import { ReactNode, useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Activity, FileText, Plus, Home, BookOpen, Heart, MessageSquare, Settings, AlertTriangle, Database, WifiOff } from 'lucide-react'
import { cn } from '@/lib/utils'
import { auditApi } from '@/lib/api'

interface LayoutProps {
  children: ReactNode
}

interface HealthStatus {
  status: string
  timestamp: string
  version: string
  environment?: string
  uptime_seconds?: number
  services?: {
    database: string
    redis: string
    nats: string
  }
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation()
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null)
  const [isHealthLoading, setIsHealthLoading] = useState(true)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await auditApi.getHealth()
        setHealthStatus(health)
      } catch (error) {
        console.error('Failed to fetch health status:', error)
      } finally {
        setIsHealthLoading(false)
      }
    }

    checkHealth()
    // Check health every 30 seconds
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Audit Logs', href: '/audit-logs', icon: FileText },
    { name: 'Create Event', href: '/create-event', icon: Plus },
    { name: 'Natural Language Query', href: '/mcp-query', icon: MessageSquare },
    { name: 'Settings', href: '/settings', icon: Settings },
    { name: 'Alert Management', href: '/alert-management', icon: AlertTriangle },
    { name: 'Event Framework', href: '/event-framework', icon: Database },
    { name: 'Outage Monitoring', href: '/outage-monitoring', icon: WifiOff },
    { name: 'Alerts', href: '/alerts', icon: AlertTriangle },
  ]

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100'
      case 'unhealthy':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-yellow-600 bg-yellow-100'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-primary-600" />
              <h1 className="ml-3 text-xl font-semibold text-gray-900">
                Audit Log Framework
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              {/* Health Status */}
              <div className="flex items-center space-x-2">
                <Heart className="w-4 h-4 text-gray-400" />
                {isHealthLoading ? (
                  <div className="w-2 h-2 bg-gray-300 rounded-full animate-pulse"></div>
                ) : healthStatus ? (
                  <div className={cn('px-2 py-1 text-xs font-medium rounded-full', getHealthColor(healthStatus.status))}>
                    {healthStatus.status}
                  </div>
                ) : (
                  <div className="px-2 py-1 text-xs font-medium rounded-full text-red-600 bg-red-100">
                    offline
                  </div>
                )}
              </div>
              
              {/* Documentation Link */}
              <a
                href={`${window.location.origin}/docs`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center px-3 py-2 text-sm font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-50 rounded-md transition-colors"
              >
                <BookOpen className="w-4 h-4 mr-2" />
                Docs
              </a>
              
              <span className="text-sm text-gray-500">
                Version 1.0.0
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <nav className="w-64 bg-white shadow-sm border-r border-gray-200 min-h-screen">
          <div className="p-4">
            <nav className="space-y-2">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={cn(
                      'flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
                      isActive
                        ? 'bg-primary-100 text-primary-700'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    )}
                  >
                    <item.icon className="mr-3 h-5 w-5" />
                    {item.name}
                  </Link>
                )
              })}
            </nav>
          </div>
        </nav>

        {/* Main content */}
        <main className="flex-1 p-8">
          {children}
        </main>
      </div>
    </div>
  )
}
