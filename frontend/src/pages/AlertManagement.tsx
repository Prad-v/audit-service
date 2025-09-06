import { useState } from 'react'
import { AlertTriangle, Filter, Bell, Settings, List } from 'lucide-react'
import { AlertRules } from './AlertRules'
import { AlertPolicies } from './AlertPolicies'
import { AlertProviders } from './AlertProviders'
import { Alerts } from './Alerts'

export function AlertManagement() {
  const [activeTab, setActiveTab] = useState<'alerts' | 'rules' | 'policies' | 'providers'>('alerts')

  const tabs = [
    {
      id: 'alerts',
      name: 'Active Alerts',
      icon: List,
      description: 'View and manage active alerts and notifications'
    },
    {
      id: 'rules',
      name: 'Alert Rules',
      icon: Filter,
      description: 'Define conditions and criteria for triggering alerts'
    },
    {
      id: 'policies',
      name: 'Alert Policies',
      icon: Settings,
      description: 'Configure alert policies and escalation rules'
    },
    {
      id: 'providers',
      name: 'Alert Providers',
      icon: Bell,
      description: 'Manage notification channels and providers'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <AlertTriangle className="w-8 h-8 text-red-600" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Alert Management</h1>
          <p className="text-gray-600 mt-1">
            Configure alert rules, policies, and notification providers for automated monitoring
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  isActive
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span>{tab.name}</span>
              </button>
            )
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'alerts' && (
          <div>
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Active Alerts</h2>
              <p className="text-gray-600">
                View and manage active alerts, notifications, and their current status.
              </p>
            </div>
            <Alerts />
          </div>
        )}
        
        {activeTab === 'rules' && (
          <div>
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Alert Rules</h2>
              <p className="text-gray-600">
                Define conditions and criteria for triggering alerts based on audit events and system metrics.
              </p>
            </div>
            <AlertRules />
          </div>
        )}
        
        {activeTab === 'policies' && (
          <div>
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Alert Policies</h2>
              <p className="text-gray-600">
                Configure alert policies with rules, severity levels, and escalation procedures.
              </p>
            </div>
            <AlertPolicies />
          </div>
        )}
        
        {activeTab === 'providers' && (
          <div>
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Alert Providers</h2>
              <p className="text-gray-600">
                Manage notification channels including Slack, PagerDuty, webhooks, and email.
              </p>
            </div>
            <AlertProviders />
          </div>
        )}
      </div>
    </div>
  )
}
