import React, { useState, useEffect } from 'react'
import { Trash2, Copy, Settings } from 'lucide-react'

interface NodePropertiesProps {
  node: any
  onUpdate: (updates: any) => void
}

export function NodeProperties({ node, onUpdate }: NodePropertiesProps) {
  const [config, setConfig] = useState(node.config || {})
  const [name, setName] = useState(node.name || '')
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

  useEffect(() => {
    setConfig(node.config || {})
    setName(node.name || '')
    setHasUnsavedChanges(false)
  }, [node])

  const handleConfigChange = (key: string, value: any) => {
    const newConfig = { ...config, [key]: value }
    setConfig(newConfig)
    setHasUnsavedChanges(true)
  }

  const handleNameChange = (newName: string) => {
    setName(newName)
    setHasUnsavedChanges(true)
  }

  const handleApplyChanges = () => {
    console.log('Applying changes:', { name, config })
    onUpdate({ 
      name: name,
      config: config 
    })
    setHasUnsavedChanges(false)
  }

  const renderNodeSpecificConfig = () => {
    switch (node.type) {
      case 'pubsub_publisher':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Project ID
              </label>
              <input
                type="text"
                value={config.project_id || ''}
                onChange={(e) => handleConfigChange('project_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="my-gcp-project"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Topic Name
              </label>
              <input
                type="text"
                value={config.topic_name || ''}
                onChange={(e) => handleConfigChange('topic_name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="my-topic"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Message Data
              </label>
              <textarea
                value={config.message_data || ''}
                onChange={(e) => handleConfigChange('message_data', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder='{"test": "message"}'
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Attributes (JSON)
              </label>
              <textarea
                value={config.attributes ? JSON.stringify(config.attributes, null, 2) : '{}'}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value)
                    handleConfigChange('attributes', parsed)
                  } catch {
                    // Invalid JSON, keep the text for editing
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder='{"key": "value"}'
              />
            </div>
          </div>
        )

      case 'pubsub_subscriber':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Project ID
              </label>
              <input
                type="text"
                value={config.project_id || ''}
                onChange={(e) => handleConfigChange('project_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="my-gcp-project"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Subscription Name
              </label>
              <input
                type="text"
                value={config.subscription_name || ''}
                onChange={(e) => handleConfigChange('subscription_name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="my-subscription"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Timeout (seconds)
              </label>
              <input
                type="number"
                value={config.timeout_seconds || 30}
                onChange={(e) => handleConfigChange('timeout_seconds', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
                max="300"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Expected Attributes (JSON)
              </label>
              <textarea
                value={config.expected_attributes ? JSON.stringify(config.expected_attributes, null, 2) : '{}'}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value)
                    handleConfigChange('expected_attributes', parsed)
                  } catch {
                    // Invalid JSON, keep the text for editing
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder='{"key": "expected_value"}'
              />
            </div>
          </div>
        )

      case 'rest_client':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                URL
              </label>
              <input
                type="url"
                value={config.url || ''}
                onChange={(e) => handleConfigChange('url', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="https://api.example.com/webhook"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Method
              </label>
              <select
                value={config.method || 'POST'}
                onChange={(e) => handleConfigChange('method', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="DELETE">DELETE</option>
                <option value="PATCH">PATCH</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Headers (JSON)
              </label>
              <textarea
                value={config.headers ? JSON.stringify(config.headers, null, 2) : '{}'}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value)
                    handleConfigChange('headers', parsed)
                  } catch {
                    // Invalid JSON, keep the text for editing
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder='{"Content-Type": "application/json"}'
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Request Body
              </label>
              <textarea
                value={config.body || ''}
                onChange={(e) => handleConfigChange('body', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder='{"key": "value"}'
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Expected Status Codes
              </label>
              <input
                type="text"
                value={config.expected_status_codes ? config.expected_status_codes.join(', ') : '200, 201, 202'}
                onChange={(e) => {
                  const codes = e.target.value.split(',').map(c => parseInt(c.trim())).filter(c => !isNaN(c))
                  handleConfigChange('expected_status_codes', codes)
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="200, 201, 202"
              />
            </div>
          </div>
        )

      case 'webhook_receiver':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Webhook URL
              </label>
              <input
                type="url"
                value={config.webhook_url || ''}
                onChange={(e) => handleConfigChange('webhook_url', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="http://localhost:8001/webhook/test123"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Expected Headers (JSON)
              </label>
              <textarea
                value={config.expected_headers ? JSON.stringify(config.expected_headers, null, 2) : '{}'}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value)
                    handleConfigChange('expected_headers', parsed)
                  } catch {
                    // Invalid JSON, keep the text for editing
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder='{"Content-Type": "application/json"}'
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Expected Body Schema (JSON)
              </label>
              <textarea
                value={config.expected_body_schema ? JSON.stringify(config.expected_body_schema, null, 2) : '{}'}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value)
                    handleConfigChange('expected_body_schema', parsed)
                  } catch {
                    // Invalid JSON, keep the text for editing
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder='{"message": "string", "timestamp": "string"}'
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Timeout (seconds)
              </label>
              <input
                type="number"
                value={config.timeout_seconds || 30}
                onChange={(e) => handleConfigChange('timeout_seconds', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
                max="300"
              />
            </div>
          </div>
        )

      case 'attribute_comparator':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source Node ID
              </label>
              <input
                type="text"
                value={config.source_node_id || ''}
                onChange={(e) => handleConfigChange('source_node_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="node_123"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Target Node ID
              </label>
              <input
                type="text"
                value={config.target_node_id || ''}
                onChange={(e) => handleConfigChange('target_node_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="node_456"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Comparisons (JSON)
              </label>
              <textarea
                value={config.comparisons ? JSON.stringify(config.comparisons, null, 2) : '[]'}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value)
                    handleConfigChange('comparisons', parsed)
                  } catch {
                    // Invalid JSON, keep the text for editing
                  }
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={4}
                placeholder='[{"attribute": "message_id", "operator": "equals", "expected_value": "123"}]'
              />
            </div>
          </div>
        )

      case 'incident_creator':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Incident Title Template
              </label>
              <input
                type="text"
                value={config.incident_title_template || 'Synthetic Test Failed: {test_name}'}
                onChange={(e) => handleConfigChange('incident_title_template', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Synthetic Test Failed: {test_name}"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Incident Description Template
              </label>
              <textarea
                value={config.incident_description_template || 'Test failed with error: {error_message}'}
                onChange={(e) => handleConfigChange('incident_description_template', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder="Test failed with error: {error_message}"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Severity
              </label>
              <select
                value={config.severity || 'medium'}
                onChange={(e) => handleConfigChange('severity', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="auto_create"
                checked={config.auto_create !== false}
                onChange={(e) => handleConfigChange('auto_create', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="auto_create" className="ml-2 block text-sm text-gray-700">
                Auto-create incidents
              </label>
            </div>
          </div>
        )

      case 'delay':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Delay (seconds)
              </label>
              <input
                type="number"
                value={config.delay_seconds || 1}
                onChange={(e) => handleConfigChange('delay_seconds', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                min="1"
                max="3600"
              />
            </div>
          </div>
        )

      case 'condition':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Condition Expression
              </label>
              <textarea
                value={config.condition_expression || ''}
                onChange={(e) => handleConfigChange('condition_expression', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                rows={3}
                placeholder="data.status === 'success'"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                True Node ID
              </label>
              <input
                type="text"
                value={config.true_node_id || ''}
                onChange={(e) => handleConfigChange('true_node_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="node_123"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                False Node ID
              </label>
              <input
                type="text"
                value={config.false_node_id || ''}
                onChange={(e) => handleConfigChange('false_node_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="node_456"
              />
            </div>
          </div>
        )

      default:
        return (
          <div className="text-center text-gray-500 py-4">
            No specific configuration for this node type.
          </div>
        )
    }
  }

  return (
    <div className="p-4 space-y-6">
      {/* Node Info */}
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Node Configuration</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Node Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter node name"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Node Type
            </label>
            <div className="px-3 py-2 bg-gray-100 rounded-md text-sm text-gray-600">
              {node.type.replace('_', ' ')}
            </div>
          </div>
        </div>
      </div>

      {/* Node-specific configuration */}
      <div>
        <h4 className="text-md font-medium text-gray-900 mb-3">Configuration</h4>
        {renderNodeSpecificConfig()}
      </div>

      {/* Actions */}
      <div className="pt-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <button
            onClick={handleApplyChanges}
            disabled={!hasUnsavedChanges}
            className={`flex-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              hasUnsavedChanges
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            {hasUnsavedChanges ? 'Apply Changes' : 'No Changes'}
          </button>
        </div>
      </div>
    </div>
  )
}
