import { useState } from 'react'
import { Cloud, Settings as SettingsIcon, Bot, Zap, ToggleLeft, Monitor } from 'lucide-react'
import { CloudProjects } from './CloudProjects'
import LLMProviders from './LLMProviders'
import { Integrations } from './Integrations'
import { FeatureFlags } from '../components/FeatureFlags'
import { AppSettings } from '../components/AppSettings'
import { useFeatureFlags } from '../contexts/FeatureFlagsContext'

export function Settings() {
  const [activeTab, setActiveTab] = useState<'cloud-projects' | 'llm-providers' | 'integrations' | 'feature-flags' | 'app-settings'>('cloud-projects')

  const tabs = [
    {
      id: 'cloud-projects',
      name: 'Cloud Projects',
      icon: Cloud,
      description: 'Manage cloud provider projects and credentials'
    },
    {
      id: 'llm-providers',
      name: 'LLM Providers',
      icon: Bot,
      description: 'Configure AI language model providers and API keys'
    },
    {
      id: 'integrations',
      name: 'Integrations',
      icon: Zap,
      description: 'Configure third-party integrations and external services'
    },
    {
      id: 'feature-flags',
      name: 'Feature Flags',
      icon: ToggleLeft,
      description: 'Enable or disable UI features and capabilities'
    },
    {
      id: 'app-settings',
      name: 'Application Settings',
      icon: Monitor,
      description: 'Customize application name and global settings'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <SettingsIcon className="w-8 h-8 text-gray-600" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-1">
            Configure system settings and integrations
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
        {activeTab === 'cloud-projects' && (
          <div>
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Cloud Projects</h2>
              <p className="text-gray-600">
                Manage your cloud provider projects, credentials, and configurations for event monitoring.
              </p>
            </div>
            <CloudProjects />
          </div>
        )}
        
        {activeTab === 'llm-providers' && (
          <div>
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">LLM Providers</h2>
              <p className="text-gray-600">
                Configure AI language model providers for natural language queries and event analysis.
              </p>
            </div>
            <LLMProviders />
          </div>
        )}
        
        {activeTab === 'integrations' && (
          <div>
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Integrations</h2>
              <p className="text-gray-600">
                Configure third-party integrations and external services for enhanced workflow automation.
              </p>
            </div>
            <Integrations />
          </div>
        )}
        
        {activeTab === 'feature-flags' && (
          <div>
            <FeatureFlags />
          </div>
        )}
        
        {activeTab === 'app-settings' && (
          <div>
            <AppSettings />
          </div>
        )}
      </div>
    </div>
  )
}


