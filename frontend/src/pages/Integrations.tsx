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
  Info,
  Zap,
  Bell,
  Webhook
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

interface StackStormConfig {
  enabled: boolean
  base_url: string
  api_key: string
  timeout: number
  retry_count: number
  ignore_ssl: boolean
}

interface PagerDutyConfig {
  enabled: boolean
  integration_key: string
  service_id: string
  escalation_policy_id: string
  severity_mapping: {
    critical: string
    high: string
    medium: string
    low: string
  }
}

interface WebhookConfig {
  enabled: boolean
  url: string
  method: 'POST' | 'PUT' | 'PATCH'
  headers: {
    [key: string]: string
  }
  timeout: number
  retry_count: number
  verify_ssl: boolean
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

const defaultStackStormConfig: StackStormConfig = {
  enabled: false,
  base_url: '',
  api_key: '',
  timeout: 30,
  retry_count: 3,
  ignore_ssl: false
}

const defaultPagerDutyConfig: PagerDutyConfig = {
  enabled: false,
  integration_key: '',
  service_id: '',
  escalation_policy_id: '',
  severity_mapping: {
    critical: 'critical',
    high: 'error',
    medium: 'warning',
    low: 'info'
  }
}

const defaultWebhookConfig: WebhookConfig = {
  enabled: false,
  url: '',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 30,
  retry_count: 3,
  verify_ssl: true
}

export function Integrations() {
  const [jiraConfig, setJiraConfig] = useState<JiraConfig>(defaultJiraConfig)
  const [stackStormConfig, setStackStormConfig] = useState<StackStormConfig>(defaultStackStormConfig)
  const [pagerDutyConfig, setPagerDutyConfig] = useState<PagerDutyConfig>(defaultPagerDutyConfig)
  const [webhookConfig, setWebhookConfig] = useState<WebhookConfig>(defaultWebhookConfig)
  
  const [showApiToken, setShowApiToken] = useState(false)
  const [showStackStormApiKey, setShowStackStormApiKey] = useState(false)
  const [showPagerDutyKey, setShowPagerDutyKey] = useState(false)
  
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveResult, setSaveResult] = useState<{ success: boolean; message: string } | null>(null)
  
  // StackStorm specific test states
  const [stackStormTesting, setStackStormTesting] = useState(false)
  const [stackStormTestResult, setStackStormTestResult] = useState<{ success: boolean; message: string } | null>(null)

  // Load configuration on component mount
  useEffect(() => {
    loadJiraConfig()
    loadStackStormConfig()
    loadPagerDutyConfig()
    loadWebhookConfig()
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

  const loadStackStormConfig = async () => {
    try {
      const response = await fetch('/api/v1/integrations/stackstorm/config')
      if (response.ok) {
        const config = await response.json()
        setStackStormConfig({ ...defaultStackStormConfig, ...config })
      }
    } catch (error) {
      console.error('Failed to load StackStorm configuration:', error)
    }
  }

  const loadPagerDutyConfig = async () => {
    try {
      const response = await fetch('/api/v1/integrations/pagerduty/config')
      if (response.ok) {
        const config = await response.json()
        setPagerDutyConfig({ ...defaultPagerDutyConfig, ...config })
      }
    } catch (error) {
      console.error('Failed to load PagerDuty configuration:', error)
    }
  }

  const loadWebhookConfig = async () => {
    try {
      const response = await fetch('/api/v1/integrations/webhook/config')
      if (response.ok) {
        const config = await response.json()
        setWebhookConfig({ ...defaultWebhookConfig, ...config })
      }
    } catch (error) {
      console.error('Failed to load Webhook configuration:', error)
    }
  }

  const handleJiraConfigChange = (field: keyof JiraConfig, value: any) => {
    setJiraConfig(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleStackStormConfigChange = (field: keyof StackStormConfig, value: any) => {
    setStackStormConfig(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handlePagerDutyConfigChange = (field: keyof PagerDutyConfig, value: any) => {
    setPagerDutyConfig(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleWebhookConfigChange = (field: keyof WebhookConfig, value: any) => {
    setWebhookConfig(prev => ({
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

  const testStackStormConnection = async () => {
    setStackStormTesting(true)
    setStackStormTestResult(null)
    
    try {
      const response = await fetch('/api/v1/integrations/stackstorm/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(stackStormConfig)
      })

      const result = await response.json()
      
      if (response.ok) {
        setStackStormTestResult({ success: true, message: 'StackStorm connection successful!' })
      } else {
        setStackStormTestResult({ success: false, message: result.detail || 'Connection failed. Please check your configuration.' })
      }
    } catch (error) {
      setStackStormTestResult({ success: false, message: 'Failed to test connection. Please try again.' })
    } finally {
      setStackStormTesting(false)
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

      {/* StackStorm Integration */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">
                  <Zap className="w-5 h-5 text-orange-600" />
                </div>
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">StackStorm Integration</h3>
                <p className="text-sm text-gray-500">
                  Connect with StackStorm for automated incident response workflows
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                stackStormConfig.enabled 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {stackStormConfig.enabled ? (
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
              <h4 className="text-sm font-medium text-gray-900">Enable StackStorm Integration</h4>
              <p className="text-sm text-gray-500">Allow triggering StackStorm actions from incidents</p>
            </div>
            <button
              onClick={() => handleStackStormConfigChange('enabled', !stackStormConfig.enabled)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                stackStormConfig.enabled ? 'bg-orange-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  stackStormConfig.enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {stackStormConfig.enabled && (
            <>
              {/* Base URL */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  StackStorm Base URL
                </label>
                <input
                  type="url"
                  value={stackStormConfig.base_url}
                  onChange={(e) => handleStackStormConfigChange('base_url', e.target.value)}
                  placeholder="https://stackstorm.your-company.com"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>

              {/* API Key */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Key
                </label>
                <div className="relative">
                  <input
                    type={showStackStormApiKey ? 'text' : 'password'}
                    value={stackStormConfig.api_key}
                    onChange={(e) => handleStackStormConfigChange('api_key', e.target.value)}
                    placeholder="Enter your StackStorm API key"
                    className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowStackStormApiKey(!showStackStormApiKey)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showStackStormApiKey ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </div>
              </div>

              {/* SSL Configuration */}
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">Ignore SSL Certificate Verification</h4>
                  <p className="text-sm text-gray-500">Skip SSL certificate validation (not recommended for production)</p>
                </div>
                <button
                  onClick={() => handleStackStormConfigChange('ignore_ssl', !stackStormConfig.ignore_ssl)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    stackStormConfig.ignore_ssl ? 'bg-orange-600' : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      stackStormConfig.ignore_ssl ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              {/* Timeout and Retry Configuration */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Timeout (seconds)
                  </label>
                  <input
                    type="number"
                    value={stackStormConfig.timeout}
                    onChange={(e) => handleStackStormConfigChange('timeout', parseInt(e.target.value))}
                    min="1"
                    max="300"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Retry Count
                  </label>
                  <input
                    type="number"
                    value={stackStormConfig.retry_count}
                    onChange={(e) => handleStackStormConfigChange('retry_count', parseInt(e.target.value))}
                    min="0"
                    max="10"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500"
                  />
                </div>
              </div>

              {/* Test Connection */}
              <div className="flex items-center space-x-4">
                <button
                  onClick={testStackStormConnection}
                  disabled={stackStormTesting || !stackStormConfig.base_url || !stackStormConfig.api_key}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <TestTube className="w-4 h-4 mr-2" />
                  {stackStormTesting ? 'Testing...' : 'Test Connectivity'}
                </button>
                
                {stackStormTestResult && (
                  <div className={`flex items-center space-x-2 ${
                    stackStormTestResult.success ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {stackStormTestResult.success ? (
                      <CheckCircle className="w-4 h-4" />
                    ) : (
                      <XCircle className="w-4 h-4" />
                    )}
                    <span className="text-sm">{stackStormTestResult.message}</span>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>

      {/* PagerDuty Integration */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">
                  <Bell className="w-5 h-5 text-red-600" />
                </div>
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">PagerDuty Integration</h3>
                <p className="text-sm text-gray-500">
                  Connect with PagerDuty for incident escalation and on-call management
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                pagerDutyConfig.enabled 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {pagerDutyConfig.enabled ? (
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
              <h4 className="text-sm font-medium text-gray-900">Enable PagerDuty Integration</h4>
              <p className="text-sm text-gray-500">Allow creating PagerDuty incidents from alerts</p>
            </div>
            <button
              onClick={() => handlePagerDutyConfigChange('enabled', !pagerDutyConfig.enabled)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                pagerDutyConfig.enabled ? 'bg-red-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  pagerDutyConfig.enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {pagerDutyConfig.enabled && (
            <>
              {/* Integration Key */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Integration Key
                </label>
                <div className="relative">
                  <input
                    type={showPagerDutyKey ? 'text' : 'password'}
                    value={pagerDutyConfig.integration_key}
                    onChange={(e) => handlePagerDutyConfigChange('integration_key', e.target.value)}
                    placeholder="Enter your PagerDuty integration key"
                    className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPagerDutyKey(!showPagerDutyKey)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPagerDutyKey ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </button>
                </div>
              </div>

              {/* Service and Escalation Policy */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Service ID
                  </label>
                  <input
                    type="text"
                    value={pagerDutyConfig.service_id}
                    onChange={(e) => handlePagerDutyConfigChange('service_id', e.target.value)}
                    placeholder="PXXXXXXXX"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Escalation Policy ID
                  </label>
                  <input
                    type="text"
                    value={pagerDutyConfig.escalation_policy_id}
                    onChange={(e) => handlePagerDutyConfigChange('escalation_policy_id', e.target.value)}
                    placeholder="PXXXXXXXX"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                  />
                </div>
              </div>

              {/* Severity Mapping */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Severity Mapping
                </label>
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(pagerDutyConfig.severity_mapping).map(([severity, level]) => (
                    <div key={severity} className="flex items-center space-x-3">
                      <span className="w-20 text-sm font-medium text-gray-700 capitalize">
                        {severity}:
                      </span>
                      <select
                        value={level}
                        onChange={(e) => handlePagerDutyConfigChange('severity_mapping', {
                          ...pagerDutyConfig.severity_mapping,
                          [severity]: e.target.value
                        })}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                      >
                        <option value="critical">Critical</option>
                        <option value="error">Error</option>
                        <option value="warning">Warning</option>
                        <option value="info">Info</option>
                      </select>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Webhook Integration */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Webhook className="w-5 h-5 text-purple-600" />
                </div>
              </div>
              <div>
                <h3 className="text-lg font-medium text-gray-900">Webhook Integration</h3>
                <p className="text-sm text-gray-500">
                  Send incident data to external systems via HTTP webhooks
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                webhookConfig.enabled 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {webhookConfig.enabled ? (
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
              <h4 className="text-sm font-medium text-gray-900">Enable Webhook Integration</h4>
              <p className="text-sm text-gray-500">Allow sending incident data to external webhooks</p>
            </div>
            <button
              onClick={() => handleWebhookConfigChange('enabled', !webhookConfig.enabled)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                webhookConfig.enabled ? 'bg-purple-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  webhookConfig.enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {webhookConfig.enabled && (
            <>
              {/* Webhook URL */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Webhook URL
                </label>
                <input
                  type="url"
                  value={webhookConfig.url}
                  onChange={(e) => handleWebhookConfigChange('url', e.target.value)}
                  placeholder="https://your-system.com/webhook"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {/* HTTP Method */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  HTTP Method
                </label>
                <select
                  value={webhookConfig.method}
                  onChange={(e) => handleWebhookConfigChange('method', e.target.value as 'POST' | 'PUT' | 'PATCH')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                  <option value="PATCH">PATCH</option>
                </select>
              </div>

              {/* Custom Headers */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Custom Headers (JSON)
                </label>
                <textarea
                  value={JSON.stringify(webhookConfig.headers, null, 2)}
                  onChange={(e) => {
                    try {
                      const headers = JSON.parse(e.target.value)
                      handleWebhookConfigChange('headers', headers)
                    } catch (error) {
                      // Invalid JSON, don't update
                    }
                  }}
                  placeholder='{"Authorization": "Bearer token", "X-Custom-Header": "value"}'
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono text-sm"
                />
              </div>

              {/* Timeout and Retry Configuration */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Timeout (seconds)
                  </label>
                  <input
                    type="number"
                    value={webhookConfig.timeout}
                    onChange={(e) => handleWebhookConfigChange('timeout', parseInt(e.target.value))}
                    min="1"
                    max="300"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Retry Count
                  </label>
                  <input
                    type="number"
                    value={webhookConfig.retry_count}
                    onChange={(e) => handleWebhookConfigChange('retry_count', parseInt(e.target.value))}
                    min="0"
                    max="10"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              {/* SSL Verification */}
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">Verify SSL Certificate</h4>
                  <p className="text-sm text-gray-500">Verify SSL certificates when making webhook requests</p>
                </div>
                <button
                  onClick={() => handleWebhookConfigChange('verify_ssl', !webhookConfig.verify_ssl)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    webhookConfig.verify_ssl ? 'bg-purple-600' : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      webhookConfig.verify_ssl ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
