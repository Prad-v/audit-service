import { useState, useEffect } from 'react'
import { 
  CheckCircle, 
  XCircle, 
  Save, 
  TestTube, 
  Eye, 
  EyeOff, 
  ExternalLink,
  AlertTriangle,
  Info
} from 'lucide-react'

interface JiraConfig {
  enabled: boolean
  instance_type: 'cloud' | 'onprem'
  base_url: string
  username: string
  api_token: string
  project_key: string
  issue_type: string
  priority_mapping: {
    critical: string
    high: string
    medium: string
    low: string
  }
  custom_fields: {
    [key: string]: string
  }
}

const defaultJiraConfig: JiraConfig = {
  enabled: false,
  instance_type: 'cloud',
  base_url: '',
  username: '',
  api_token: '',
  project_key: '',
  issue_type: 'Bug',
  priority_mapping: {
    critical: 'Highest',
    high: 'High',
    medium: 'Medium',
    low: 'Low'
  },
  custom_fields: {}
}

export function Integrations() {
  const [jiraConfig, setJiraConfig] = useState<JiraConfig>(defaultJiraConfig)
  const [showApiToken, setShowApiToken] = useState(false)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveResult, setSaveResult] = useState<{ success: boolean; message: string } | null>(null)

  // Load configuration on component mount
  useEffect(() => {
    loadJiraConfig()
  }, [])

  const loadJiraConfig = async () => {
    try {
      const response = await fetch('/api/v1/integrations/jira/config')
      if (response.ok) {
        const config = await response.json()
        setJiraConfig({ ...defaultJiraConfig, ...config })
      }
    } catch (error) {
      console.error('Failed to load Jira configuration:', error)
    }
  }

  const handleJiraConfigChange = (field: keyof JiraConfig, value: any) => {
    setJiraConfig(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handlePriorityMappingChange = (severity: string, priority: string) => {
    setJiraConfig(prev => ({
      ...prev,
      priority_mapping: {
        ...prev.priority_mapping,
        [severity]: priority
      }
    }))
  }

  const testJiraConnection = async () => {
    setTesting(true)
    setTestResult(null)
    
    try {
      const response = await fetch('/api/v1/integrations/jira/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(jiraConfig)
      })

      const result = await response.json()
      
      if (response.ok) {
        setTestResult({ success: true, message: 'Connection successful! Jira integration is working.' })
      } else {
        setTestResult({ success: false, message: result.detail || 'Connection failed. Please check your configuration.' })
      }
    } catch (error) {
      setTestResult({ success: false, message: 'Failed to test connection. Please try again.' })
    } finally {
      setTesting(false)
    }
  }

  const saveJiraConfig = async () => {
    setSaving(true)
    setSaveResult(null)
    
    try {
      const response = await fetch('/api/v1/integrations/jira/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(jiraConfig)
      })

      const result = await response.json()
      
      if (response.ok) {
        setSaveResult({ success: true, message: 'Jira configuration saved successfully!' })
        // Audit the configuration change
        await auditConfigurationChange('jira', 'configuration_updated', jiraConfig)
      } else {
        setSaveResult({ success: false, message: result.detail || 'Failed to save configuration.' })
      }
    } catch (error) {
      setSaveResult({ success: false, message: 'Failed to save configuration. Please try again.' })
    } finally {
      setSaving(false)
    }
  }

  const auditConfigurationChange = async (integration: string, action: string, config: any) => {
    try {
      await fetch('/api/v1/audit-logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: `${integration}_${action}`,
          resource_type: 'integration_configuration',
          resource_id: integration,
          details: {
            integration,
            action,
            config_changed: Object.keys(config).filter(key => key !== 'api_token'), // Don't log sensitive data
            timestamp: new Date().toISOString()
          },
          user_id: 'current_user', // This should be replaced with actual user ID
          ip_address: '127.0.0.1' // This should be replaced with actual IP
        })
      })
    } catch (error) {
      console.error('Failed to audit configuration change:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Jira Integration */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <ExternalLink className="w-5 h-5 text-blue-600" />
                </div>
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">Jira Integration</h3>
                <p className="text-sm text-gray-500">
                  Connect with Jira to automatically create tickets for incidents
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                jiraConfig.enabled 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {jiraConfig.enabled ? (
                  <>
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Enabled
                  </>
                ) : (
                  <>
                    <XCircle className="w-3 h-3 mr-1" />
                    Disabled
                  </>
                )}
              </span>
            </div>
          </div>
        </div>

        <div className="px-6 py-4 space-y-6">
          {/* Enable/Disable Toggle */}
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-gray-900">Enable Jira Integration</h4>
              <p className="text-sm text-gray-500">Allow creating Jira tickets from incidents</p>
            </div>
            <button
              onClick={() => handleJiraConfigChange('enabled', !jiraConfig.enabled)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                jiraConfig.enabled ? 'bg-blue-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  jiraConfig.enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {jiraConfig.enabled && (
            <>
              {/* Instance Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Jira Instance Type
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => handleJiraConfigChange('instance_type', 'cloud')}
                    className={`p-4 border rounded-lg text-left transition-colors ${
                      jiraConfig.instance_type === 'cloud'
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <div className="font-medium text-gray-900">Jira Cloud</div>
                    <div className="text-sm text-gray-500">Atlassian-hosted Jira</div>
                  </button>
                  <button
                    onClick={() => handleJiraConfigChange('instance_type', 'onprem')}
                    className={`p-4 border rounded-lg text-left transition-colors ${
                      jiraConfig.instance_type === 'onprem'
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <div className="font-medium text-gray-900">Jira On-Premise</div>
                    <div className="text-sm text-gray-500">Self-hosted Jira Server/Data Center</div>
                  </button>
                </div>
              </div>

              {/* Base URL */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Jira Base URL
                </label>
                <input
                  type="url"
                  value={jiraConfig.base_url}
                  onChange={(e) => handleJiraConfigChange('base_url', e.target.value)}
                  placeholder={jiraConfig.instance_type === 'cloud' 
                    ? 'https://your-domain.atlassian.net' 
                    : 'https://jira.your-company.com'
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="mt-1 text-sm text-gray-500">
                  {jiraConfig.instance_type === 'cloud' 
                    ? 'Your Atlassian cloud instance URL'
                    : 'Your on-premise Jira server URL'
                  }
                </p>
              </div>

              {/* Username */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Username / Email
                </label>
                <input
                  type="text"
                  value={jiraConfig.username}
                  onChange={(e) => handleJiraConfigChange('username', e.target.value)}
                  placeholder={jiraConfig.instance_type === 'cloud' 
                    ? 'your-email@company.com' 
                    : 'your-username'
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* API Token */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Token
                </label>
                <div className="relative">
                  <input
                    type={showApiToken ? 'text' : 'password'}
                    value={jiraConfig.api_token}
                    onChange={(e) => handleJiraConfigChange('api_token', e.target.value)}
                    placeholder="Enter your API token"
                    className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiToken(!showApiToken)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showApiToken ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </div>
                <div className="mt-2 p-3 bg-blue-50 rounded-md">
                  <div className="flex">
                    <Info className="h-4 w-4 text-blue-400 mt-0.5 mr-2" />
                    <div className="text-sm text-blue-700">
                      <p className="font-medium">How to get your API token:</p>
                      <ul className="mt-1 list-disc list-inside space-y-1">
                        <li>Go to <a href="https://id.atlassian.com/manage-profile/security/api-tokens" target="_blank" rel="noopener noreferrer" className="underline">Atlassian Account Settings</a></li>
                        <li>Click "Create API token"</li>
                        <li>Give it a label and copy the token</li>
                        <li>For on-premise: Use your password or personal access token</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              {/* Project Configuration */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Project Key
                  </label>
                  <input
                    type="text"
                    value={jiraConfig.project_key}
                    onChange={(e) => handleJiraConfigChange('project_key', e.target.value.toUpperCase())}
                    placeholder="PROJ"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Issue Type
                  </label>
                  <select
                    value={jiraConfig.issue_type}
                    onChange={(e) => handleJiraConfigChange('issue_type', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="Bug">Bug</option>
                    <option value="Task">Task</option>
                    <option value="Story">Story</option>
                    <option value="Incident">Incident</option>
                    <option value="Problem">Problem</option>
                  </select>
                </div>
              </div>

              {/* Priority Mapping */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Priority Mapping
                </label>
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(jiraConfig.priority_mapping).map(([severity, priority]) => (
                    <div key={severity} className="flex items-center space-x-3">
                      <span className="w-20 text-sm font-medium text-gray-700 capitalize">
                        {severity}:
                      </span>
                      <select
                        value={priority}
                        onChange={(e) => handlePriorityMappingChange(severity, e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="Highest">Highest</option>
                        <option value="High">High</option>
                        <option value="Medium">Medium</option>
                        <option value="Low">Low</option>
                        <option value="Lowest">Lowest</option>
                      </select>
                    </div>
                  ))}
                </div>
              </div>

              {/* Test Connection */}
              <div className="flex items-center space-x-4">
                <button
                  onClick={testJiraConnection}
                  disabled={testing || !jiraConfig.base_url || !jiraConfig.username || !jiraConfig.api_token}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <TestTube className="w-4 h-4 mr-2" />
                  {testing ? 'Testing...' : 'Test Connection'}
                </button>
                
                {testResult && (
                  <div className={`flex items-center space-x-2 ${
                    testResult.success ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {testResult.success ? (
                      <CheckCircle className="w-4 h-4" />
                    ) : (
                      <XCircle className="w-4 h-4" />
                    )}
                    <span className="text-sm">{testResult.message}</span>
                  </div>
                )}
              </div>

              {/* Save Configuration */}
              <div className="flex items-center space-x-4">
                <button
                  onClick={saveJiraConfig}
                  disabled={saving}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {saving ? 'Saving...' : 'Save Configuration'}
                </button>
                
                {saveResult && (
                  <div className={`flex items-center space-x-2 ${
                    saveResult.success ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {saveResult.success ? (
                      <CheckCircle className="w-4 h-4" />
                    ) : (
                      <XCircle className="w-4 h-4" />
                    )}
                    <span className="text-sm">{saveResult.message}</span>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Future Integrations Placeholder */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">More Integrations Coming Soon</h3>
          <p className="text-sm text-gray-500">
            We're working on adding more integrations to enhance your workflow
          </p>
        </div>
        <div className="px-6 py-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 border border-gray-200 rounded-lg text-center">
              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                <AlertTriangle className="w-5 h-5 text-gray-400" />
              </div>
              <h4 className="font-medium text-gray-900">PagerDuty</h4>
              <p className="text-sm text-gray-500">Incident escalation and on-call management</p>
            </div>
            <div className="p-4 border border-gray-200 rounded-lg text-center">
              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                <AlertTriangle className="w-5 h-5 text-gray-400" />
              </div>
              <h4 className="font-medium text-gray-900">Slack</h4>
              <p className="text-sm text-gray-500">Team notifications and collaboration</p>
            </div>
            <div className="p-4 border border-gray-200 rounded-lg text-center">
              <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                <AlertTriangle className="w-5 h-5 text-gray-400" />
              </div>
              <h4 className="font-medium text-gray-900">Microsoft Teams</h4>
              <p className="text-sm text-gray-500">Enterprise communication and alerts</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
