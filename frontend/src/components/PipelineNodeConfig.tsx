import React, { useState, useEffect } from 'react'
import { X, Save, TestTube, Eye, EyeOff } from 'lucide-react'

interface EventNode {
  id: string
  type: 'event_subscription' | 'event_processor' | 'event_sink'
  name: string
  config: any
  position: { x: number; y: number }
  status: 'idle' | 'running' | 'error' | 'success'
  metrics?: {
    eventsPerSecond?: number
    totalEvents?: number
    lastProcessed?: string
    errorCount?: number
  }
  validationErrors?: string[]
  // Event management specific fields
  eventSubscriptionId?: string
  eventProcessorId?: string
  eventSinkId?: string
}

interface PipelineNodeConfigProps {
  node: EventNode | null
  isOpen: boolean
  onClose: () => void
  onSave: (nodeId: string, config: any) => void
  onTest?: (nodeId: string) => void
}

const PipelineNodeConfig: React.FC<PipelineNodeConfigProps> = ({
  node,
  isOpen,
  onClose,
  onSave,
  onTest
}) => {
  const [config, setConfig] = useState<any>({})
  const [isValid, setIsValid] = useState(true)
  const [showAdvanced, setShowAdvanced] = useState(false)

  useEffect(() => {
    if (node) {
      setConfig({ ...node.config })
    }
  }, [node])

  const validateConfig = (config: any, type: string) => {
    switch (type) {
      case 'event_subscription':
        return config.type && config.endpoint
      case 'event_processor':
        return config.type && config.rules
      case 'event_sink':
        return config.type && config.endpoint
      default:
        return true
    }
  }

  const handleConfigChange = (key: string, value: any) => {
    const newConfig = { ...config, [key]: value }
    setConfig(newConfig)
    if (node) {
      setIsValid(validateConfig(newConfig, node.type))
    }
  }

  const handleSave = () => {
    if (!isValid || !node) {
      return
    }
    
    onSave(node.id, config)
    onClose()
  }

  const renderEventSubscriptionConfig = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Subscription Type
        </label>
        <select
          value={config.type || ''}
          onChange={(e) => handleConfigChange('type', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select subscription type</option>
          <option value="webhook">Webhook</option>
          <option value="file">File Watcher</option>
          <option value="syslog">Syslog</option>
          <option value="kafka">Kafka Consumer</option>
          <option value="http">HTTP Client</option>
          <option value="pubsub">Pub/Sub</option>
          <option value="kinesis">Kinesis</option>
          <option value="nats">NATS</option>
        </select>
      </div>

      {config.type === 'webhook' && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Endpoint
            </label>
            <input
              type="text"
              value={config.endpoint || ''}
              onChange={(e) => handleConfigChange('endpoint', e.target.value)}
              placeholder="/api/webhook/events"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              HTTP Method
            </label>
            <select
              value={config.method || 'POST'}
              onChange={(e) => handleConfigChange('method', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="PATCH">PATCH</option>
            </select>
          </div>
        </>
      )}

      {config.type === 'file' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            File Path Pattern
          </label>
          <input
            type="text"
            value={config.path || ''}
            onChange={(e) => handleConfigChange('path', e.target.value)}
            placeholder="/var/log/events/*.log"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}

      {config.type === 'kafka' && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Bootstrap Servers
            </label>
            <input
              type="text"
              value={config.bootstrapServers || ''}
              onChange={(e) => handleConfigChange('bootstrapServers', e.target.value)}
              placeholder="kafka:9092"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Topic
            </label>
            <input
              type="text"
              value={config.topic || ''}
              onChange={(e) => handleConfigChange('topic', e.target.value)}
              placeholder="audit-events"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </>
      )}
    </div>
  )

  const renderEventProcessorConfig = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Processor Type
        </label>
        <select
          value={config.type || ''}
          onChange={(e) => handleConfigChange('type', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select processor type</option>
          <option value="transformer">Transformer</option>
          <option value="filter">Filter</option>
          <option value="enricher">Enricher</option>
          <option value="aggregator">Aggregator</option>
          <option value="sampler">Sampler</option>
          <option value="deduplicator">Deduplicator</option>
        </select>
      </div>

      {config.type === 'transformer' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Transformation Rules
          </label>
          <textarea
            value={JSON.stringify(config.rules || [], null, 2)}
            onChange={(e) => {
              try {
                const rules = JSON.parse(e.target.value)
                handleConfigChange('rules', rules)
              } catch (error) {
                // Invalid JSON, keep as string for now
              }
            }}
            placeholder="Enter transformation rules as JSON"
            rows={6}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
          />
          <p className="text-xs text-gray-500 mt-1">
            Define field mappings, transformations, and data modifications
          </p>
        </div>
      )}

      {config.type === 'filter' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Filter Conditions
          </label>
          <textarea
            value={JSON.stringify(config.rules || [], null, 2)}
            onChange={(e) => {
              try {
                const rules = JSON.parse(e.target.value)
                handleConfigChange('rules', rules)
              } catch (error) {
                // Invalid JSON, keep as string for now
              }
            }}
            placeholder="Enter filter conditions as JSON"
            rows={6}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
          />
          <p className="text-xs text-gray-500 mt-1">
            Define conditions for filtering events (e.g., field values, ranges)
          </p>
        </div>
      )}

      {config.type === 'enricher' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Enrichment Rules
          </label>
          <textarea
            value={JSON.stringify(config.rules || [], null, 2)}
            onChange={(e) => {
              try {
                const rules = JSON.parse(e.target.value)
                handleConfigChange('rules', rules)
              } catch (error) {
                // Invalid JSON, keep as string for now
              }
            }}
            placeholder="Enter enrichment rules as JSON"
            rows={6}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
          />
          <p className="text-xs text-gray-500 mt-1">
            Define fields to add, external data lookups, and metadata enrichment
          </p>
        </div>
      )}
    </div>
  )

  const renderEventSinkConfig = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Sink Type
        </label>
        <select
          value={config.type || ''}
          onChange={(e) => handleConfigChange('type', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select sink type</option>
          <option value="http">HTTP Endpoint</option>
          <option value="elasticsearch">Elasticsearch</option>
          <option value="kafka">Kafka Producer</option>
          <option value="s3">S3 Storage</option>
          <option value="database">Database</option>
          <option value="file">File Output</option>
          <option value="console">Console Output</option>
        </select>
      </div>

      {config.type === 'http' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Endpoint URL
          </label>
          <input
            type="text"
            value={config.endpoint || ''}
            onChange={(e) => handleConfigChange('endpoint', e.target.value)}
            placeholder="https://api.example.com/events"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}

      {config.type === 'elasticsearch' && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Elasticsearch Endpoint
            </label>
            <input
              type="text"
              value={config.endpoint || ''}
              onChange={(e) => handleConfigChange('endpoint', e.target.value)}
              placeholder="http://elasticsearch:9200"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Index Name
            </label>
            <input
              type="text"
              value={config.index || ''}
              onChange={(e) => handleConfigChange('index', e.target.value)}
              placeholder="audit-events"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </>
      )}

      {config.type === 'kafka' && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Bootstrap Servers
            </label>
            <input
              type="text"
              value={config.bootstrapServers || ''}
              onChange={(e) => handleConfigChange('bootstrapServers', e.target.value)}
              placeholder="kafka:9092"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Topic
            </label>
            <input
              type="text"
              value={config.topic || ''}
              onChange={(e) => handleConfigChange('topic', e.target.value)}
              placeholder="processed-events"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </>
      )}

      {config.type === 'database' && (
        <>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Database Type
            </label>
            <select
              value={config.databaseType || ''}
              onChange={(e) => handleConfigChange('databaseType', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select database type</option>
              <option value="postgresql">PostgreSQL</option>
              <option value="mysql">MySQL</option>
              <option value="mongodb">MongoDB</option>
              <option value="redis">Redis</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Connection String
            </label>
            <input
              type="text"
              value={config.connectionString || ''}
              onChange={(e) => handleConfigChange('connectionString', e.target.value)}
              placeholder="postgresql://user:pass@host:port/db"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </>
      )}
    </div>
  )

  const renderNodeConfig = () => {
    if (!node) return <div>Unknown node type</div>

    switch (node.type) {
      case 'event_subscription':
        return renderEventSubscriptionConfig()
      case 'event_processor':
        return renderEventProcessorConfig()
      case 'event_sink':
        return renderEventSinkConfig()
      default:
        return <div>Unknown node type</div>
    }
  }

  if (!isOpen || !node) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Configure {node.name}
            </h2>
            <p className="text-sm text-gray-600 capitalize">
              {node.type.replace('_', ' ')} Configuration
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          <div className="space-y-6">
            {/* Basic Configuration */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Node Name
              </label>
              <input
                type="text"
                value={node.name}
                disabled
                className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
              />
            </div>

            {/* Event management specific info */}
            {node.eventSubscriptionId && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Event Subscription ID
                </label>
                <input
                  type="text"
                  value={node.eventSubscriptionId}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                />
              </div>
            )}

            {node.eventProcessorId && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Event Processor ID
                </label>
                <input
                  type="text"
                  value={node.eventProcessorId}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                />
              </div>
            )}

            {node.eventSinkId && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Event Sink ID
                </label>
                <input
                  type="text"
                  value={node.eventSinkId}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
                />
              </div>
            )}

            {/* Type-specific Configuration */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Configuration</h3>
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center text-sm text-gray-600 hover:text-gray-900"
                >
                  {showAdvanced ? <EyeOff className="w-4 h-4 mr-1" /> : <Eye className="w-4 h-4 mr-1" />}
                  {showAdvanced ? 'Hide' : 'Show'} Advanced
                </button>
              </div>
              
              {renderNodeConfig()}
            </div>

            {/* Advanced Options */}
            {showAdvanced && (
              <div className="space-y-4 pt-4 border-t border-gray-200">
                <h4 className="text-md font-medium text-gray-900">Advanced Options</h4>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Batch Size
                  </label>
                  <input
                    type="number"
                    value={config.batchSize || 1000}
                    onChange={(e) => handleConfigChange('batchSize', parseInt(e.target.value))}
                    min="1"
                    max="10000"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Batch Timeout (ms)
                  </label>
                  <input
                    type="number"
                    value={config.batchTimeout || 1000}
                    onChange={(e) => handleConfigChange('batchTimeout', parseInt(e.target.value))}
                    min="100"
                    max="60000"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Retry Attempts
                  </label>
                  <input
                    type="number"
                    value={config.retryAttempts || 3}
                    onChange={(e) => handleConfigChange('retryAttempts', parseInt(e.target.value))}
                    min="0"
                    max="10"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center space-x-2">
            {onTest && (
              <button
                onClick={() => onTest(node.id)}
                className="flex items-center px-4 py-2 bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
              >
                <TestTube className="w-4 h-4 mr-2" />
                Test Configuration
              </button>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={!isValid}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-4 h-4 mr-2" />
              Save Configuration
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PipelineNodeConfig
